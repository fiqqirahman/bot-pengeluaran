from datetime import date

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from expense_bot.analysis import build_summary, top_expenses
from expense_bot.categorizer import choose_category
from expense_bot.config import Config
from expense_bot.parser import ParseError, parse_expense_message, parse_month_arg
from expense_bot.repository import ExpenseRepository

def build_application(config: Config) -> Application:
    repository = ExpenseRepository(config.database_url)
    application = Application.builder().token(config.telegram_bot_token).build()

    application.bot_data["repository"] = repository

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("summary", summary))
    application.add_handler(CommandHandler("top", top))
    application.add_handler(CommandHandler("recent", recent))
    application.add_handler(CommandHandler("category", category))
    application.add_handler(CommandHandler("edit", edit))
    application.add_handler(CommandHandler("delete_last", delete_last))
    application.add_handler(CommandHandler("delete", delete))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, record_expense))

    return application

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Kirim pengeluaran seperti: makan siang 35000")

async def record_expense(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    repository = _repository(context)
    try:
        parsed = parse_expense_message(update.message.text)
        category_name = choose_category(parsed.description, parsed.explicit_category)
        record = repository.create_expense(
            telegram_user_id=update.effective_user.id,
            parsed=parsed,
            category=category_name,
            spent_at=update.message.date,
        )
    except ParseError as exc:
        await update.message.reply_text(str(exc))
        return

    await update.message.reply_text(
        f"Tersimpan #{record.id}: {_rupiah(record.amount)} - {record.description} ({record.category})"
    )

async def summary(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    repository = _repository(context)
    try:
        year, month = parse_month_arg(" ".join(context.args), today=date.today())
    except ParseError as exc:
        await update.message.reply_text(str(exc))
        return

    records = repository.list_month(update.effective_user.id, year, month)
    expense_summary = build_summary(records)
    lines = [f"Summary {year:04d}-{month:02d}", f"Total: {_rupiah(expense_summary.total)}"]

    if expense_summary.category_totals:
        lines.append("Kategori terbesar:")
        for category_name, total in sorted(
            expense_summary.category_totals.items(),
            key=lambda item: item[1],
            reverse=True,
        ):
            lines.append(f"- {category_name}: {_rupiah(total)}")

    if expense_summary.largest:
        largest = expense_summary.largest
        lines.append(f"Terbesar: #{largest.id} {_rupiah(largest.amount)} - {largest.description}")

    await update.message.reply_text("\n".join(lines))

async def top(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    repository = _repository(context)
    try:
        year, month = parse_month_arg(" ".join(context.args), today=date.today())
    except ParseError as exc:
        await update.message.reply_text(str(exc))
        return

    records = top_expenses(repository.list_month(update.effective_user.id, year, month))
    if not records:
        await update.message.reply_text(f"Belum ada pengeluaran untuk {year:04d}-{month:02d}.")
        return

    lines = [f"Top pengeluaran {year:04d}-{month:02d}:"]
    for record in records:
        lines.append(f"#{record.id} {_rupiah(record.amount)} - {record.description} ({record.category})")
    await update.message.reply_text("\n".join(lines))

async def recent(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    records = _repository(context).recent(update.effective_user.id)
    if not records:
        await update.message.reply_text("Belum ada pengeluaran.")
        return

    lines = ["Transaksi terbaru:"]
    for record in records:
        lines.append(f"#{record.id} {_rupiah(record.amount)} - {record.description} ({record.category})")
    await update.message.reply_text("\n".join(lines))

async def category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Format: /category transport")
        return

    records = _repository(context).recent(update.effective_user.id, limit=1)
    if not records:
        await update.message.reply_text("Belum ada transaksi untuk dikoreksi.")
        return

    category_name = " ".join(context.args).strip().lower()
    updated = _repository(context).update_category(update.effective_user.id, records[0].id, category_name)
    await update.message.reply_text(
        f"Kategori #{updated.id} diubah: {updated.description} ({updated.category})"
    )

async def edit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) < 3 or context.args[1].lower() != "kategori":
        await update.message.reply_text("Format: /edit 12 kategori transport")
        return

    try:
        expense_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("ID transaksi harus angka.")
        return

    category_name = " ".join(context.args[2:]).strip().lower()
    updated = _repository(context).update_category(update.effective_user.id, expense_id, category_name)
    if not updated:
        await update.message.reply_text(f"Transaksi #{expense_id} tidak ditemukan.")
        return

    await update.message.reply_text(
        f"Kategori #{updated.id} diubah: {updated.description} ({updated.category})"
    )

async def delete_last(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    records = _repository(context).recent(update.effective_user.id, limit=1)
    if not records:
        await update.message.reply_text("Belum ada transaksi untuk dihapus.")
        return

    deleted = _repository(context).delete_expense(update.effective_user.id, records[0].id)
    await update.message.reply_text(f"Dihapus #{deleted.id}: {_rupiah(deleted.amount)} - {deleted.description}")

async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Format: /delete 12")
        return

    try:
        expense_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("ID transaksi harus angka.")
        return

    deleted = _repository(context).delete_expense(update.effective_user.id, expense_id)
    if not deleted:
        await update.message.reply_text(f"Transaksi #{expense_id} tidak ditemukan.")
        return

    await update.message.reply_text(f"Dihapus #{deleted.id}: {_rupiah(deleted.amount)} - {deleted.description}")

def _repository(context: ContextTypes.DEFAULT_TYPE) -> ExpenseRepository:
    return context.application.bot_data["repository"]

def _rupiah(amount: int) -> str:
    return f"Rp{amount:,}".replace(",", ".")
