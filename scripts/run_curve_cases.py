# -*- coding: utf-8 -*-
"""按文档 CmbPREngine run 的 7 个案例跑通，并用自造行情对照是否写死。"""
from __future__ import print_function

import copy
import json
import sys
import urllib.error
import urllib.request

BASE = "http://localhost:8080/api/quant"

# ---------------------------------------------------------------------------
# Init：文档配方 + 文档惯例 + 补齐文档任务用到但惯例样例缺失的条目
# ---------------------------------------------------------------------------
def recipe(*items):
    return {"buildRecipes": list(items)}


R_FR007 = {"curveName": "CNY FR007", "currency": "CNY", "createMethod": "BOOTSTRAP", "dayCountConvention": "ACT/365"}
R_SHIBOR = {"curveName": "CNY SHIBOR 3M", "currency": "CNY", "createMethod": "BOOTSTRAP", "dayCountConvention": "ACT/365"}
R_SOFR = {"curveName": "USD SOFR", "currency": "USD", "createMethod": "BOOTSTRAP", "dayCountConvention": "ACT/365"}
R_CNY_FX = {"curveName": "CNY FX ONSHORE", "currency": "CNY", "createMethod": "BOOTSTRAP", "dayCountConvention": "ACT/365"}
R_USD_FX = {
    "curveName": "USD FX ONSHORE",
    "currency": "USD",
    "baseCurve": "CNY FX ONSHORE",
    "baseCurveCurrency": "CNY",
    "currencyPair": "USD/CNY",
    "createMethod": "IMPLY",
    "dayCountConvention": "ACT/365",
}
R_VOL = {"curveName": "USD-CNY-FX_VOL", "currency": "USD", "createMethod": "VOL", "currencyPair": "USD/CNY"}

CALENDAR = {
    "calendars": [
        {
            "center": "BEJ",
            "holidays": [
                "2025-01-01", "2025-01-28", "2025-01-29", "2025-01-30", "2025-01-31",
                "2025-10-01", "2025-10-02", "2025-10-03",
                "2026-01-01", "2026-02-17", "2026-02-18", "2026-10-01",
            ],
            "busDays": ["2025-01-26", "2026-02-14"],
        },
        {
            "center": "NYC",
            "holidays": [
                "2025-01-01", "2025-01-20", "2025-02-17", "2025-05-26", "2025-07-04",
                "2025-09-01", "2025-11-27", "2025-12-25",
                "2026-01-01", "2026-01-19", "2026-02-16", "2026-05-25", "2026-07-03",
            ],
            "busDays": [],
        },
        {
            "center": "USGS",
            "holidays": ["2025-01-01", "2025-12-25", "2026-01-01", "2026-07-03"],
            "busDays": [],
        },
        {
            "center": "TARGET",
            "holidays": ["2025-01-01", "2025-04-18", "2025-12-25", "2026-01-01"],
            "busDays": [],
        },
    ]
}

CONVENTIONS = {
    "Cash Deposit": [
        {
            "conventionName": "CNY-CASH-DEPOSIT",
            "center": "BEJ",
            "description": "Cash Deposit",
            "attributes": {
                "SettlementOffset": "1B",
                "SettlementHolidays": "BEJ",
                "Currency": "CNY",
                "Notional": "10000000",
                "AccrualBasis": "Act/365",
                "PaymentBusinessDayConvention": "MF",
                "PaymentHolidays": "BEJ",
                "TermOverride": "",
                "Type": "Cash Deposit",
            },
        },
        {
            "conventionName": "SHIBOR",
            "center": "BEJ",
            "description": "Cash Deposit",
            "attributes": {
                "SettlementOffset": "1B",
                "SettlementHolidays": "BEJ",
                "Currency": "CNY",
                "Notional": "10000000",
                "AccrualBasis": "Act/360",
                "PaymentBusinessDayConvention": "MF",
                "PaymentHolidays": "BEJ",
                "TermOverride": "",
                "Type": "Cash Deposit",
            },
        },
        {
            "conventionName": "SHIBOR-ON",
            "center": "BEJ",
            "description": "Cash Deposit",
            "attributes": {
                "SettlementOffset": "0B",
                "SettlementHolidays": "BEJ",
                "Currency": "CNY",
                "Notional": "10000000",
                "AccrualBasis": "Act/360",
                "PaymentBusinessDayConvention": "MF",
                "PaymentHolidays": "BEJ",
                "TermOverride": "1B",
                "Type": "Cash Deposit",
            },
        },
        {
            "conventionName": "USD-CASH-DEPOSIT",
            "center": "NYC",
            "description": "Cash Deposit",
            "attributes": {
                "SettlementOffset": "2B",
                "SettlementHolidays": "NYC",
                "Currency": "USD",
                "Notional": "1000000",
                "AccrualBasis": "Act/360",
                "PaymentBusinessDayConvention": "MF",
                "PaymentHolidays": "NYC",
                "TermOverride": "",
                "Type": "Cash Deposit",
            },
        },
    ],
    "Swap": [
        {
            "conventionName": "CNY-SWAP-QTR-MONEY",
            "center": "BEJ",
            "description": "Swap",
            "attributes": {
                "SettlementOffset": "1B",
                "SettlementHolidays": "BEJ",
                "Currency": "CNY",
                "Notional": "10000000",
                "LiborIndex": "CNY-SHIBOR-3M",
                "AccrualPeriod": "3M",
                "AccrualBasis": "Act/365F",
                "PaymentBusinessDayConvention": "MF",
                "PaymentHolidays": "BEJ",
                "Type": "Swap",
            },
        }
    ],
    "FRA": [
        {
            "conventionName": "SOFR-1B-FRA",
            "center": "NYC",
            "description": "FRA",
            "attributes": {
                "SettlementOffset": "0b",
                "SettlementHolidays": "USGS",
                "Currency": "USD",
                "Notional": "1000000",
                "LiborIndex": "SOFR-1B",
                "AccrualBasis": "Act/365F",
                "PaymentBusinessDayConvention": "MF",
                "PaymentHolidays": "NYC",
                "Type": "FRA",
            },
        }
    ],
    "Overnight Index Future": [
        {
            "conventionName": "SOFR-FUTURE-3M",
            "center": "NYC",
            "description": "Overnight Index Future",
            "attributes": {
                "RateCutOffDaysOffset": "1B",
                "Currency": "USD",
                "ContractNotional": "1000000",
                "OvernightIndex": "SOFR-1B",
                "AverageType": "COMPOUND",
                "Tenor": "3M",
                "PaymentOffset": "2B",
                "PaymentBusinessDayConvention": "MF",
                "PaymentHolidays": "TARGET",
                "BasisPointValue": "25",
                "Type": "Overnight Index Future",
            },
        }
    ],
    "Overnight Index Swap": [
        {
            "conventionName": "SOFR-OIS",
            "center": "NYC",
            "description": "Overnight Index Swap",
            "attributes": {
                "SettlementOffset": "2B",
                "SettlementHolidays": "NYC",
                "Currency": "USD",
                "Notional": "1000000",
                "OvernightIndex": "SOFR-1B",
                "AverageType": "COMPOUND",
                "AccrualPeriod": "1Y",
                "AccrualBasis": "Act/360",
                "RateCutOffDaysOffset": "1B",
                "PaymentOffset": "2B",
                "PaymentBusinessDayConvention": "MF",
                "PaymentHolidays": "NYC",
                "Type": "Overnight Index Swap",
            },
        },
        {
            "conventionName": "USD-SOFR-OIS",
            "center": "NYC",
            "description": "Overnight Index Swap",
            "attributes": {
                "SettlementOffset": "2B",
                "SettlementHolidays": "NYC",
                "Currency": "USD",
                "Notional": "1000000",
                "OvernightIndex": "SOFR-1B",
                "AverageType": "COMPOUND",
                "AccrualPeriod": "1Y",
                "AccrualBasis": "Act/360",
                "RateCutOffDaysOffset": "1B",
                "PaymentOffset": "2B",
                "PaymentBusinessDayConvention": "MF",
                "PaymentHolidays": "NYC",
                "Type": "Overnight Index Swap",
            },
        },
        {
            "conventionName": "SOFR OIS",
            "center": "NYC",
            "description": "Overnight Index Swap",
            "attributes": {
                "SettlementOffset": "2B",
                "SettlementHolidays": "NYC",
                "Currency": "USD",
                "Notional": "1000000",
                "OvernightIndex": "SOFR-1B",
                "AverageType": "COMPOUND",
                "AccrualPeriod": "1Y",
                "AccrualBasis": "Act/360",
                "RateCutOffDaysOffset": "1B",
                "PaymentOffset": "2B",
                "PaymentBusinessDayConvention": "MF",
                "PaymentHolidays": "NYC",
                "Type": "Overnight Index Swap",
            },
        },
    ],
    "FX Rate": [
        {
            "conventionName": "USD-CNY",
            "attributes": {
                "Id": "USD-CNY",
                "BaseCurrency": "USD",
                "BaseFixingBusDayConv": "F",
                "BaseFixingHolidays": "NYC",
                "BaseFixingOffset": "0b",
                "QuotedCurrency": "CNY",
                "QuotedFixingBusDayConv": "F",
                "SettlementBusDayConv": "F",
                "SettlementHolidays": "NYC+BEJ",
                "QuotedFixingHolidays": "BEJ",
                "QuotedFixingOffset": "2b",
                "Type": "FX Rate",
            },
        },
        {
            "conventionName": "USD/CNY",
            "attributes": {
                "Id": "USD/CNY",
                "BaseCurrency": "USD",
                "BaseFixingBusDayConv": "F",
                "BaseFixingHolidays": "NYC",
                "BaseFixingOffset": "0b",
                "QuotedCurrency": "CNY",
                "QuotedFixingBusDayConv": "F",
                "SettlementBusDayConv": "F",
                "SettlementHolidays": "NYC+BEJ",
                "QuotedFixingHolidays": "BEJ",
                "QuotedFixingOffset": "2b",
                "Type": "FX Rate",
            },
        },
    ],
}


def q(curve, inst_type, inst_name, tenor, quote, pair="", strike=""):
    row = {
        "curveName": curve,
        "pair": pair,
        "instrumentType": inst_type,
        "instrumentName": inst_name,
        "tenor": tenor,
        "quote": quote,
        "strike": strike,
    }
    if tenor is None:
        del row["tenor"]
    return row


def task(task_id, valuation_date, quotes, static_id, market_id):
    return {
        "schema_version": "1.0",
        "task_id": task_id,
        "task_type": "BUILD_MODELS",
        "valuation_date": valuation_date,
        "snapshots": {
            "static_snapshot_id": static_id,
            "market_snapshot_id": market_id,
        },
        "market_input": {
            "market_data_set": {
                "market_quote": quotes,
            }
        },
    }


def bump_rate_quotes(quotes, bp, skip_types):
    out = []
    for row in quotes:
        copied = copy.deepcopy(row)
        if copied.get("instrumentType") not in skip_types:
            copied["quote"] = round(float(copied["quote"]) + bp / 10000.0, 10)
        out.append(copied)
    return out


def scale_quotes(quotes, types, factor):
    out = []
    for row in quotes:
        copied = copy.deepcopy(row)
        if copied.get("instrumentType") in types:
            copied["quote"] = round(float(copied["quote"]) * factor, 10)
        out.append(copied)
    return out


# ① 文档 FR007
FR007_DOC = [
    q("CNY FR007", "Cash Deposit", "CNY-CASH-DEPOSIT", "O/N", 0.013139),
    q("CNY FR007", "Cash Deposit", "CNY-CASH-DEPOSIT", "1W", 0.022),
    q("CNY FR007", "Cash Deposit", "CNY-CASH-DEPOSIT", "2W", 0.019),
    q("CNY FR007", "Swap", "CNY-SWAP-QTR-MONEY", "1M", 0.0165125),
    q("CNY FR007", "Swap", "CNY-SWAP-QTR-MONEY", "3M", 0.0157625),
    q("CNY FR007", "Swap", "CNY-SWAP-QTR-MONEY", "6M", 0.01525),
    q("CNY FR007", "Swap", "CNY-SWAP-QTR-MONEY", "9M", 0.015021),
    q("CNY FR007", "Swap", "CNY-SWAP-QTR-MONEY", "1Y", 0.014985),
    q("CNY FR007", "Swap", "CNY-SWAP-QTR-MONEY", "2Y", 0.0151375),
    q("CNY FR007", "Swap", "CNY-SWAP-QTR-MONEY", "3Y", 0.0154195),
    q("CNY FR007", "Swap", "CNY-SWAP-QTR-MONEY", "4Y", 0.0157505),
    q("CNY FR007", "Swap", "CNY-SWAP-QTR-MONEY", "5Y", 0.0161165),
    q("CNY FR007", "Swap", "CNY-SWAP-QTR-MONEY", "7Y", 0.016872),
    q("CNY FR007", "Swap", "CNY-SWAP-QTR-MONEY", "10Y", 0.017933),
    q("CNY FR007", "Swap", "CNY-SWAP-QTR-MONEY", "20Y", 0.01775),
    q("CNY FR007", "Swap", "CNY-SWAP-QTR-MONEY", "30Y", 0.0172),
]

# 自造：2024 年末常见 FR007 形态——短端约 1.6%，长端缓升到 2.1%，无文档 1W=2.2% 尖刺
FR007_SYN = [
    q("CNY FR007", "Cash Deposit", "CNY-CASH-DEPOSIT", "O/N", 0.0160),
    q("CNY FR007", "Cash Deposit", "CNY-CASH-DEPOSIT", "1W", 0.0162),
    q("CNY FR007", "Cash Deposit", "CNY-CASH-DEPOSIT", "2W", 0.0164),
    q("CNY FR007", "Swap", "CNY-SWAP-QTR-MONEY", "1M", 0.0168),
    q("CNY FR007", "Swap", "CNY-SWAP-QTR-MONEY", "3M", 0.0172),
    q("CNY FR007", "Swap", "CNY-SWAP-QTR-MONEY", "6M", 0.0176),
    q("CNY FR007", "Swap", "CNY-SWAP-QTR-MONEY", "9M", 0.0180),
    q("CNY FR007", "Swap", "CNY-SWAP-QTR-MONEY", "1Y", 0.0184),
    q("CNY FR007", "Swap", "CNY-SWAP-QTR-MONEY", "2Y", 0.0190),
    q("CNY FR007", "Swap", "CNY-SWAP-QTR-MONEY", "3Y", 0.0195),
    q("CNY FR007", "Swap", "CNY-SWAP-QTR-MONEY", "5Y", 0.0200),
    q("CNY FR007", "Swap", "CNY-SWAP-QTR-MONEY", "7Y", 0.0204),
    q("CNY FR007", "Swap", "CNY-SWAP-QTR-MONEY", "10Y", 0.0208),
    q("CNY FR007", "Swap", "CNY-SWAP-QTR-MONEY", "30Y", 0.0210),
]

SHIBOR_DOC = [
    q("CNY SHIBOR 3M", "Cash Deposit", "SHIBOR", "O/N", 0.01327),
    q("CNY SHIBOR 3M", "Cash Deposit", "SHIBOR", "1W", 0.01956),
    q("CNY SHIBOR 3M", "Cash Deposit", "SHIBOR", "2W", 0.01951),
    q("CNY SHIBOR 3M", "Cash Deposit", "SHIBOR", "1M", 0.01588),
    q("CNY SHIBOR 3M", "Cash Deposit", "SHIBOR", "3M", 0.016),
    q("CNY SHIBOR 3M", "Cash Deposit", "SHIBOR", "6M", 0.01888),
    q("CNY SHIBOR 3M", "Cash Deposit", "SHIBOR", "9M", 0.01914),
    q("CNY SHIBOR 3M", "Swap", "CNY-SWAP-QTR-MONEY", "1Y", 0.015775),
    q("CNY SHIBOR 3M", "Swap", "CNY-SWAP-QTR-MONEY", "2Y", 0.0159425),
    q("CNY SHIBOR 3M", "Swap", "CNY-SWAP-QTR-MONEY", "3Y", 0.0163315),
    q("CNY SHIBOR 3M", "Swap", "CNY-SWAP-QTR-MONEY", "4Y", 0.016683),
    q("CNY SHIBOR 3M", "Swap", "CNY-SWAP-QTR-MONEY", "5Y", 0.017175),
    q("CNY SHIBOR 3M", "Swap", "CNY-SWAP-QTR-MONEY", "6Y", 0.037),
    q("CNY SHIBOR 3M", "Swap", "CNY-SWAP-QTR-MONEY", "7Y", 0.017861),
    q("CNY SHIBOR 3M", "Swap", "CNY-SWAP-QTR-MONEY", "10Y", 0.0186125),
]

# 自造：修正文档 6Y=3.7% 尖刺，改成平滑 1.75%；整体再抬 20bp
SHIBOR_SYN = [
    q("CNY SHIBOR 3M", "Cash Deposit", "SHIBOR", "O/N", 0.0155),
    q("CNY SHIBOR 3M", "Cash Deposit", "SHIBOR", "1W", 0.0160),
    q("CNY SHIBOR 3M", "Cash Deposit", "SHIBOR", "1M", 0.0168),
    q("CNY SHIBOR 3M", "Cash Deposit", "SHIBOR", "3M", 0.0175),
    q("CNY SHIBOR 3M", "Cash Deposit", "SHIBOR", "6M", 0.0180),
    q("CNY SHIBOR 3M", "Swap", "CNY-SWAP-QTR-MONEY", "1Y", 0.0182),
    q("CNY SHIBOR 3M", "Swap", "CNY-SWAP-QTR-MONEY", "2Y", 0.0186),
    q("CNY SHIBOR 3M", "Swap", "CNY-SWAP-QTR-MONEY", "3Y", 0.0190),
    q("CNY SHIBOR 3M", "Swap", "CNY-SWAP-QTR-MONEY", "5Y", 0.0196),
    q("CNY SHIBOR 3M", "Swap", "CNY-SWAP-QTR-MONEY", "7Y", 0.0200),
    q("CNY SHIBOR 3M", "Swap", "CNY-SWAP-QTR-MONEY", "10Y", 0.0205),
]

SOFR_OLD_DOC = [
    q("USD SOFR", "RFR FRA", "SOFR-1B-FRA", "1D", 0.00362),
    q("USD SOFR", "RFR Future", "SOFR-FUTURE-3M", "2026-06-26", 96.3025),
    q("USD SOFR", "RFR Swap", "SOFR OIS", "2Y", 0.0395345),
]

SOFR_OLD_SYN = [
    q("USD SOFR", "RFR FRA", "SOFR-1B-FRA", "1D", 0.0433),
    q("USD SOFR", "RFR Future", "SOFR-FUTURE-3M", "2026-09-16", 95.50),
    q("USD SOFR", "RFR Swap", "SOFR OIS", "2Y", 0.0410),
]

SOFR_NEW_DOC = [
    q("USD SOFR", "Cash Deposit", "USD-CASH-DEPOSIT", "1D", 0.00362),
    q("USD SOFR", "Cash Deposit", "USD-CASH-DEPOSIT", "1W", 0.0362),
    q("USD SOFR", "Cash Deposit", "USD-CASH-DEPOSIT", "1M", 0.0368),
    q("USD SOFR", "Cash Deposit", "USD-CASH-DEPOSIT", "3M", 0.0375),
    q("USD SOFR", "Overnight Index Swap", "USD-SOFR-OIS", "6M", 0.0381),
    q("USD SOFR", "Overnight Index Swap", "USD-SOFR-OIS", "1Y", 0.0387),
    q("USD SOFR", "Overnight Index Swap", "USD-SOFR-OIS", "2Y", 0.0395345),
    q("USD SOFR", "Overnight Index Swap", "USD-SOFR-OIS", "3Y", 0.0398),
    q("USD SOFR", "Overnight Index Swap", "USD-SOFR-OIS", "5Y", 0.0402),
    q("USD SOFR", "Overnight Index Swap", "USD-SOFR-OIS", "7Y", 0.0405),
    q("USD SOFR", "Overnight Index Swap", "USD-SOFR-OIS", "10Y", 0.0408),
]

# 自造：2024 中常见倒挂 SOFR——隔夜 5.33%，10Y 约 4.0%
SOFR_NEW_SYN = [
    q("USD SOFR", "Cash Deposit", "USD-CASH-DEPOSIT", "1D", 0.0533),
    q("USD SOFR", "Cash Deposit", "USD-CASH-DEPOSIT", "1W", 0.0531),
    q("USD SOFR", "Cash Deposit", "USD-CASH-DEPOSIT", "1M", 0.0528),
    q("USD SOFR", "Cash Deposit", "USD-CASH-DEPOSIT", "3M", 0.0515),
    q("USD SOFR", "Overnight Index Swap", "USD-SOFR-OIS", "6M", 0.0495),
    q("USD SOFR", "Overnight Index Swap", "USD-SOFR-OIS", "1Y", 0.0470),
    q("USD SOFR", "Overnight Index Swap", "USD-SOFR-OIS", "2Y", 0.0445),
    q("USD SOFR", "Overnight Index Swap", "USD-SOFR-OIS", "5Y", 0.0415),
    q("USD SOFR", "Overnight Index Swap", "USD-SOFR-OIS", "10Y", 0.0400),
]

CNY_FX_DOC = [
    q("CNY FX ONSHORE", "Cash Deposit", "SHIBOR-ON", "O/N", 0.013139),
    q("CNY FX ONSHORE", "Cash Deposit", "SHIBOR", "1W", 0.022),
    q("CNY FX ONSHORE", "Cash Deposit", "SHIBOR", "1M", 0.0165125),
    q("CNY FX ONSHORE", "Swap", "CNY-SWAP-QTR-MONEY", "3M", 0.0157625),
    q("CNY FX ONSHORE", "Swap", "CNY-SWAP-QTR-MONEY", "6M", 0.01525),
    q("CNY FX ONSHORE", "Swap", "CNY-SWAP-QTR-MONEY", "9M", 0.015021),
    q("CNY FX ONSHORE", "Swap", "CNY-SWAP-QTR-MONEY", "1Y", 0.014985),
]

CNY_FX_SYN = [
    q("CNY FX ONSHORE", "Cash Deposit", "SHIBOR-ON", "O/N", 0.0180),
    q("CNY FX ONSHORE", "Cash Deposit", "SHIBOR", "1W", 0.0185),
    q("CNY FX ONSHORE", "Cash Deposit", "SHIBOR", "1M", 0.0190),
    q("CNY FX ONSHORE", "Swap", "CNY-SWAP-QTR-MONEY", "3M", 0.0195),
    q("CNY FX ONSHORE", "Swap", "CNY-SWAP-QTR-MONEY", "6M", 0.0200),
    q("CNY FX ONSHORE", "Swap", "CNY-SWAP-QTR-MONEY", "1Y", 0.0208),
    q("CNY FX ONSHORE", "Swap", "CNY-SWAP-QTR-MONEY", "5Y", 0.0220),
]

USD_FX_DOC = CNY_FX_DOC + [
    q("USD FX ONSHORE", "FX Spot", "USD/CNY", None, 6.7935, pair="USD/CNY"),
    q("USD FX ONSHORE", "Swap point", "USD/CNY", "1M", -0.0125, pair="USD/CNY"),
    q("USD FX ONSHORE", "Swap point", "USD/CNY", "3M", -0.0375, pair="USD/CNY"),
    q("USD FX ONSHORE", "Swap point", "USD/CNY", "6M", -0.075, pair="USD/CNY"),
    q("USD FX ONSHORE", "Swap point", "USD/CNY", "1Y", -0.15, pair="USD/CNY"),
]

# 自造：USD/CNY 即期 7.10，掉期点改为正向升水（美元利率更高时常见）
USD_FX_SYN = CNY_FX_SYN + [
    q("USD FX ONSHORE", "FX Spot", "USD/CNY", None, 7.1000, pair="USD/CNY"),
    q("USD FX ONSHORE", "Swap point", "USD/CNY", "1M", 0.0200, pair="USD/CNY"),
    q("USD FX ONSHORE", "Swap point", "USD/CNY", "3M", 0.0550, pair="USD/CNY"),
    q("USD FX ONSHORE", "Swap point", "USD/CNY", "6M", 0.1100, pair="USD/CNY"),
    q("USD FX ONSHORE", "Swap point", "USD/CNY", "1Y", 0.2100, pair="USD/CNY"),
]

VOL_DOC = USD_FX_DOC + [
    q("USD-CNY-FX_VOL", "Vol", "USD/CNY", "1W", 0.062, pair="USD/CNY", strike="ATM"),
    q("USD-CNY-FX_VOL", "Vol", "USD/CNY", "1M", 0.0635, pair="USD/CNY", strike="ATM"),
    q("USD-CNY-FX_VOL", "Vol", "USD/CNY", "3M", 0.065, pair="USD/CNY", strike="ATM"),
    q("USD-CNY-FX_VOL", "Vol", "USD/CNY", "6M", 0.0675, pair="USD/CNY", strike="ATM"),
    q("USD-CNY-FX_VOL", "Vol", "USD/CNY", "1Y", 0.072, pair="USD/CNY", strike="ATM"),
    q("USD-CNY-FX_VOL", "Vol", "USD/CNY", "2Y", 0.078, pair="USD/CNY", strike="ATM"),
    q("USD-CNY-FX_VOL", "Vol", "USD/CNY", "1M", 0.009, pair="USD/CNY", strike="RR 25"),
    q("USD-CNY-FX_VOL", "Vol", "USD/CNY", "6M", 0.011, pair="USD/CNY", strike="RR 25"),
    q("USD-CNY-FX_VOL", "Vol", "USD/CNY", "1Y", 0.012, pair="USD/CNY", strike="RR 25"),
    q("USD-CNY-FX_VOL", "Vol", "USD/CNY", "1M", 0.0035, pair="USD/CNY", strike="BFY 25"),
    q("USD-CNY-FX_VOL", "Vol", "USD/CNY", "6M", 0.0045, pair="USD/CNY", strike="BFY 25"),
    q("USD-CNY-FX_VOL", "Vol", "USD/CNY", "1Y", 0.005, pair="USD/CNY", strike="BFY 25"),
]

# 自造：高波动年 ATM 提到 10%，RR/BF 同步放大
VOL_SYN = USD_FX_SYN + [
    q("USD-CNY-FX_VOL", "Vol", "USD/CNY", "1W", 0.095, pair="USD/CNY", strike="ATM"),
    q("USD-CNY-FX_VOL", "Vol", "USD/CNY", "1M", 0.098, pair="USD/CNY", strike="ATM"),
    q("USD-CNY-FX_VOL", "Vol", "USD/CNY", "3M", 0.102, pair="USD/CNY", strike="ATM"),
    q("USD-CNY-FX_VOL", "Vol", "USD/CNY", "6M", 0.108, pair="USD/CNY", strike="ATM"),
    q("USD-CNY-FX_VOL", "Vol", "USD/CNY", "1Y", 0.115, pair="USD/CNY", strike="ATM"),
    q("USD-CNY-FX_VOL", "Vol", "USD/CNY", "2Y", 0.122, pair="USD/CNY", strike="ATM"),
    q("USD-CNY-FX_VOL", "Vol", "USD/CNY", "1M", 0.015, pair="USD/CNY", strike="RR 25"),
    q("USD-CNY-FX_VOL", "Vol", "USD/CNY", "1Y", 0.020, pair="USD/CNY", strike="RR 25"),
    q("USD-CNY-FX_VOL", "Vol", "USD/CNY", "1M", 0.006, pair="USD/CNY", strike="BFY 25"),
    q("USD-CNY-FX_VOL", "Vol", "USD/CNY", "1Y", 0.008, pair="USD/CNY", strike="BFY 25"),
]


CONV_IR = {
    "Cash Deposit": CONVENTIONS["Cash Deposit"],
    "Swap": CONVENTIONS["Swap"],
}
CONV_SOFR_NEW = {
    "Cash Deposit": CONVENTIONS["Cash Deposit"],
    "Overnight Index Swap": CONVENTIONS["Overnight Index Swap"],
}
CONV_SOFR_OLD = {
    "FRA": CONVENTIONS["FRA"],
    "Overnight Index Future": CONVENTIONS["Overnight Index Future"],
    "Overnight Index Swap": CONVENTIONS["Overnight Index Swap"],
}
CONV_FX = {
    "Cash Deposit": CONVENTIONS["Cash Deposit"],
    "Swap": CONVENTIONS["Swap"],
    "FX Rate": CONVENTIONS["FX Rate"],
}

CASES = [
    {
        "id": "1",
        "name": "CNY FR007",
        "recipe": recipe(R_FR007),
        "conventions": CONV_IR,
        "doc": task("CNY FR007", "2025-12-31", FR007_DOC, "STATIC-20251331-v1", "MKT-20251231-v2232"),
        "syn": task("CNY FR007 SYN", "2025-12-31", FR007_SYN, "STATIC-SYN-FR007", "MKT-SYN-FR007"),
        "metric": "M_ZC_RATE",
        "curve": "CNY FR007",
    },
    {
        "id": "2",
        "name": "CNY SHIBOR 3M",
        "recipe": recipe(R_SHIBOR),
        "conventions": CONV_IR,
        "doc": task("appnew-shibor-3m", "2025-12-31", SHIBOR_DOC, "STATIC-20251231-v1", "MKT-20251231-v2232"),
        "syn": task("shibor-syn", "2025-12-31", SHIBOR_SYN, "STATIC-SYN-SHIBOR", "MKT-SYN-SHIBOR"),
        "metric": "M_ZC_RATE",
        "curve": "CNY SHIBOR 3M",
    },
    {
        "id": "3",
        "name": "USD SOFR (旧/Future)",
        "recipe": recipe(R_SOFR),
        "conventions": CONV_SOFR_OLD,
        "doc": task("usd-sofr-1", "2026-06-30", SOFR_OLD_DOC, "STATIC-20260630-v1", "MKT-20260630-v2232"),
        "syn": task("usd-sofr-old-syn", "2026-06-30", SOFR_OLD_SYN, "STATIC-SYN-SOFR-OLD", "MKT-SYN-SOFR-OLD"),
        "metric": "M_ZC_RATE",
        "curve": "USD SOFR",
    },
    {
        "id": "4",
        "name": "USD SOFR (新/Cash+OIS)",
        "recipe": recipe(R_SOFR),
        "conventions": CONV_SOFR_NEW,
        "doc": task("usd-sofr-1", "2026-06-30", SOFR_NEW_DOC, "STATIC-20260630-v1", "MKT-20260630-v2232"),
        "syn": task("usd-sofr-new-syn", "2026-06-30", SOFR_NEW_SYN, "STATIC-SYN-SOFR-NEW", "MKT-SYN-SOFR-NEW"),
        "metric": "M_ZC_RATE",
        "curve": "USD SOFR",
    },
    {
        "id": "5",
        "name": "CNY FX ONSHORE",
        "recipe": recipe(R_CNY_FX),
        "conventions": CONV_IR,
        "doc": task("cny-fx-onshore", "2025-12-31", CNY_FX_DOC, "STATIC-20251231-v1", "MKT-20251231-v2232"),
        "syn": task("cny-fx-syn", "2025-12-31", CNY_FX_SYN, "STATIC-SYN-CNYFX", "MKT-SYN-CNYFX"),
        "metric": "M_ZC_RATE",
        "curve": "CNY FX ONSHORE",
    },
    {
        "id": "6",
        "name": "USD FX ONSHORE",
        "recipe": recipe(R_CNY_FX, R_USD_FX),
        "conventions": CONV_FX,
        "doc": task("usd-fx-onshore", "2025-12-31", USD_FX_DOC, "STATIC-20251231-v1", "MKT-20251231-v2232"),
        "syn": task("usd-fx-syn", "2025-12-31", USD_FX_SYN, "STATIC-SYN-USDFX", "MKT-SYN-USDFX"),
        "metric": "M_ZC_RATE",
        "curve": "USD FX ONSHORE",
    },
    {
        "id": "7",
        "name": "USD-CNY-FX_VOL",
        "recipe": recipe(R_CNY_FX, R_USD_FX, R_VOL),
        "conventions": CONV_FX,
        "doc": task("usd-cny-vol-surface", "2025-12-31", VOL_DOC, "STATIC-20251231-v1", "MKT-20251231-v2232"),
        "syn": task("usd-cny-vol-syn", "2025-12-31", VOL_SYN, "STATIC-SYN-VOL", "MKT-SYN-VOL"),
        "metric": "M_VOL",
        "curve": "USD-CNY-FX_VOL",
    },
]


def post_json(path, payload):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        BASE + path,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as ex:
        body = ex.read().decode("utf-8")
        try:
            return json.loads(body)
        except Exception:
            return {"success": False, "code": str(ex.code), "message": body, "data": None}


def oneshot(payload, build_recipe, conventions):
    return post_json(
        "/run/oneshot",
        {
            "parseMode": "TASK",
            "resetBeforeInit": True,
            "buildRecipe": build_recipe,
            "calendar": CALENDAR,
            "conventions": conventions,
            "payload": payload,
        },
    )


def extract_task(resp):
    data = resp.get("data") or {}
    workflow = data.get("workflow") or {}
    tasks = workflow.get("tasks") or []
    if not tasks:
        return {
            "http_ok": resp.get("success"),
            "http_code": resp.get("code"),
            "http_msg": resp.get("message"),
            "status": None,
            "error": resp.get("message"),
            "rows": [],
        }
    task_view = tasks[0]
    err = task_view.get("error")
    table = task_view.get("resultTable") or {}
    headers = table.get("headers") or []
    data_rows = table.get("data") or []
    return {
        "http_ok": resp.get("success"),
        "http_code": resp.get("code"),
        "http_msg": resp.get("message"),
        "status": task_view.get("status"),
        "error": None if err is None else "%s:%s" % (err.get("code"), err.get("message")),
        "headers": headers,
        "rows": data_rows,
        "elapsed": task_view.get("elapsedMillis"),
    }


def index_of(headers, name):
    try:
        return headers.index(name)
    except ValueError:
        return -1


def summarize(parsed, metric, curve_name):
    headers = parsed.get("headers") or []
    rows = parsed.get("rows") or []
    i_metric = index_of(headers, metric)
    i_curve = index_of(headers, "M_CURVE")
    i_gen = index_of(headers, "M_GENERATOR")
    i_pillar = index_of(headers, "M_PILLAR")
    i_mat = index_of(headers, "M_MATURITY")
    i_strike = index_of(headers, "M_STRIKE")
    values = []
    labels = []
    for row in rows:
        if i_curve >= 0 and curve_name and row[i_curve] != curve_name:
            # VOL 样本输出 M_GENERATOR=USD/CNY，不一定有 M_CURVE
            if metric != "M_VOL":
                continue
        if i_metric < 0:
            continue
        values.append(row[i_metric])
        pillar = row[i_pillar] if i_pillar >= 0 else (row[i_mat] if i_mat >= 0 else "")
        strike = row[i_strike] if i_strike >= 0 else ""
        labels.append("%s|%s" % (pillar, strike))
    return labels, values


def judge(doc_parsed, syn_parsed, doc_vals, syn_vals):
    if doc_parsed.get("status") != "SUCCESS" and syn_parsed.get("status") != "SUCCESS":
        return "两边都失败（更像缺能力/缺 init，不像写死）"
    if doc_parsed.get("status") == "SUCCESS" and syn_parsed.get("status") != "SUCCESS":
        return "文档样例成功、自造行情失败（输入敏感，非写死；或自造数不合法）"
    if doc_parsed.get("status") != "SUCCESS" and syn_parsed.get("status") == "SUCCESS":
        return "文档样例失败、自造行情成功（文档入参本身有问题）"
    if not doc_vals or not syn_vals:
        return "成功但无结果行，无法判断"
    if doc_vals == syn_vals:
        return "疑似写死：行情改了，结果向量完全相同"
    return "真实计算：行情变化后面结果跟着变"


def fmt_head(vals, labels, n=3):
    if not vals:
        return "-"
    pairs = []
    for i, val in enumerate(vals[:n]):
        label = labels[i] if i < len(labels) else ""
        pairs.append("%s=%s" % (label, val))
    return "; ".join(pairs)


def main():
    print("BASE", BASE)
    health = urllib.request.urlopen(BASE + "/health", timeout=5).read().decode("utf-8")
    print("health", health)
    print("")
    results = []
    for case in CASES:
        print("=" * 72)
        print("[%s] %s" % (case["id"], case["name"]))
        doc_resp = oneshot(case["doc"], case["recipe"], case["conventions"])
        syn_resp = oneshot(case["syn"], case["recipe"], case["conventions"])
        doc_p = extract_task(doc_resp)
        syn_p = extract_task(syn_resp)
        doc_labels, doc_vals = summarize(doc_p, case["metric"], case["curve"])
        syn_labels, syn_vals = summarize(syn_p, case["metric"], case["curve"])
        verdict = judge(doc_p, syn_p, doc_vals, syn_vals)
        print("  DOC  status=%s error=%s rows=%d elapsed=%s" % (
            doc_p.get("status"), doc_p.get("error"), len(doc_p.get("rows") or []), doc_p.get("elapsed")))
        if doc_p.get("status") != "SUCCESS":
            print("  DOC  http=%s %s" % (doc_p.get("http_code"), doc_p.get("http_msg")))
        print("  DOC  %s sample: %s" % (case["metric"], fmt_head(doc_vals, doc_labels)))
        print("  SYN  status=%s error=%s rows=%d elapsed=%s" % (
            syn_p.get("status"), syn_p.get("error"), len(syn_p.get("rows") or []), syn_p.get("elapsed")))
        if syn_p.get("status") != "SUCCESS":
            print("  SYN  http=%s %s" % (syn_p.get("http_code"), syn_p.get("http_msg")))
        print("  SYN  %s sample: %s" % (case["metric"], fmt_head(syn_vals, syn_labels)))
        print("  判定: %s" % verdict)
        results.append({
            "id": case["id"],
            "name": case["name"],
            "doc_status": doc_p.get("status"),
            "doc_error": doc_p.get("error"),
            "doc_rows": len(doc_p.get("rows") or []),
            "syn_status": syn_p.get("status"),
            "syn_error": syn_p.get("error"),
            "syn_rows": len(syn_p.get("rows") or []),
            "verdict": verdict,
            "doc_sample": fmt_head(doc_vals, doc_labels),
            "syn_sample": fmt_head(syn_vals, syn_labels),
        })
    print("")
    print("=" * 72)
    print("汇总")
    for item in results:
        print("%s %-22s DOC=%-8s SYN=%-8s  %s" % (
            item["id"], item["name"], item["doc_status"] or "N/A", item["syn_status"] or "N/A", item["verdict"]))
    out_path = "scripts/curve_case_results.json"
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(results, handle, ensure_ascii=False, indent=2)
    print("结果已写", out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
