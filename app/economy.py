"Blueprint file containing all economy-related commands and handlers"
# pylint: disable=unused-argument,missing-function-docstring
import config
from flask_discord_interactions import Context, DiscordInteractionsBlueprint, Embed, Message
from flask_discord_interactions.models.embed import Author, Field
from flask_discord_interactions.models.option import CommandOptionType, Option
from flask_discord_interactions.models.user import User
from i18n import t
from resources import items, jobs, levels, players, trucks
from resources.autocompletes import amount_all
from utils import commatize, get_localizations

economy_bp = DiscordInteractionsBlueprint()


@economy_bp.custom_handler(custom_id="job_show")
def show_job(ctx: Context, player_id: str) -> Message:
    player = players.get(player_id)

    current_job = player.get_job()
    if current_job is None:
        raise players.WrongPlayer()
    job_embed = Embed(
        color=config.EMBED_COLOR,
        author=Author(name=t("job.title", player=player.name), icon_url=ctx.author.avatar_url),
        fields=[],
    )
    item = items.get(current_job.place_from.produced_item)
    job_message = t(
        "job.message",
        place_to=current_job.place_to,
        item=item,
        place_from=current_job.place_from,
        reward=commatize(current_job.reward),
    )
    job_embed.fields.append(Field(name=t("job.current"), value=job_message, inline=False))
    job_embed.fields.append(Field(name=t("job.state.current"), value=jobs.get_state(current_job)))
    return Message(embed=job_embed, ephemeral=True)


@economy_bp.custom_handler(custom_id="refill")
def refill(ctx: Context, player_id: str):
    player = players.get(ctx.author.id, check=player_id)
    gas_amount = trucks.get(player.truck_id).gas_capacity - player.gas
    price = round(gas_amount * 1.2)

    try:
        player.debit_money(price)
    except players.NotEnoughMoney:
        if player.gas < 170:
            if player.level > 2:
                player.level -= 2
            player.gas += 100
            player.xp = 0
            return Message(
                t("refill.not_enough_money.deal", player_id=ctx.author.id),
                ephemeral=True,
            )
        return Message(
            t("refill.not_enough_money.jobs", player_id=ctx.author.id),
            ephemeral=True,
        )

    refill_embed = Embed(
        title=t("refill.success.title"),
        description=t("refill.success.description", amount=gas_amount, price=price),
        color=config.EMBED_COLOR,
    )

    player.gas = trucks.get(player.truck_id).gas_capacity
    drive_embed = ctx.message.embeds[1]
    drive_embed.fields[2]["value"] = str(player.gas)

    return Message(
        embeds=[ctx.message.embeds[0], drive_embed, refill_embed], update=True, components=ctx.message.components
    )


@economy_bp.command(
    name=t("commands.give.name", locale=config.I18n.FALLBACK),
    name_localizations=get_localizations("commands.give.name"),
    description=t("commands.give.description", locale=config.I18n.FALLBACK),
    description_localizations=get_localizations("commands.give.description"),
    options=[
        Option(
            name=t("commands.give.options.user.name", locale=config.I18n.FALLBACK),
            name_localizations=get_localizations("commands.give.options.user.name"),
            description=t("commands.give.options.user.description", locale=config.I18n.FALLBACK),
            description_localizations=get_localizations("commands.give.options.user.description"),
            type=CommandOptionType.USER,
            required=True,
        ),
        Option(
            name=t("commands.give.options.amount.name", locale=config.I18n.FALLBACK),
            name_localizations=get_localizations("commands.give.options.amount.name"),
            description=t("commands.give.options.amount.description", locale=config.I18n.FALLBACK),
            description_localizations=get_localizations("commands.give.options.amount.description"),
            type=CommandOptionType.INTEGER,
            min_value=1,
            max_value=1000000,
            autocomplete=True,
            required=True,
        ),
    ],
)
def give(ctx: Context, user: User, amount: int) -> Message:
    """Transfers money to a specific user."""
    acceptor = players.get(user.id)
    donator = players.get(ctx.author.id)

    if ctx.author.id == acceptor.id:
        return Message(
            embed=Embed(
                title=t("give.errors.title", name=ctx.author.username),
                description=t("give.errors.self"),
                color=config.EMBED_COLOR,
            )
        )

    cap = levels.coincap(acceptor.level)
    if amount > cap:
        return Message(
            embed=Embed(
                title=t("give.errors.title", name=ctx.author.username),
                description=t("give.errors.cap", cap=commatize(cap)),
                color=config.EMBED_COLOR,
            )
        )

    donator.debit_money(amount)
    acceptor.add_money(amount)
    return Message(
        embed=Embed(
            description=t("give.success", amount=commatize(amount), donator=donator.name, acceptor=acceptor),
            color=config.EMBED_COLOR,
        )
    )


economy_bp.add_autocomplete_handler(amount_all, "give")
