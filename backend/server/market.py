from flask import Blueprint, jsonify, request

from server.market_service import build_market_history, list_instruments
from server.utils import err, parse_date

market_bp = Blueprint("market", __name__, url_prefix="/market")


@market_bp.route("/instruments", methods=["GET"])
def get_instruments():
    return jsonify(list_instruments())


@market_bp.route("/history", methods=["GET"])
def get_history():
    symbol = request.args.get("symbol")
    if not symbol:
        return err("Missing required query param: symbol", 400)

    end_date = None
    raw_end = request.args.get("end_date")
    if raw_end:
        try:
            end_date = parse_date(raw_end)
        except ValueError:
            return err(f"Invalid end_date: {raw_end!r}", 400)

    history_days = 130
    raw_days = request.args.get("days")
    if raw_days is not None:
        try:
            history_days = int(raw_days)
            if history_days <= 0:
                raise ValueError
        except (ValueError, TypeError):
            return err("days must be a positive integer", 400)

    try:
        payload = build_market_history(
            symbol,
            end_date=end_date,
            history_days=history_days,
        )
    except ValueError as exc:
        return err(str(exc), 400)

    return jsonify(payload)
