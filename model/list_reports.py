from app_config import REPORT_MODULE_PATH

# live_time - время жизни отчета в часах, может указываться с 2 занками после запятой
# в этом случае время минимальное жизни отчета составляет 36 секунд


dict_reports = {
    "ДИА": {
        "1500": {
            "module_dir": f"{REPORT_MODULE_PATH}.DIA",
            "live_time": "1",
            "01": {
                "name": "Количество иждивенцев и сумма 0701 за период",
                "proc": "rep_dia_0701_01",
                "data_approve": "13.02.2023",
                "author": "Гусейнов Ш.",
                "params": {"date_first": "C", "date_second": "по"},
            },
            "02": {
                "name": "Списочный состав иждивенцев",
                "proc": "rep_dia_0701_02",
                "data_approve": "14.02.2023",
                "author": "Гусейнов Ш.",
                "params": {"date_first": "C", "date_second": "по"},
            },
            "03": {
                "name": "Списочный состав получателей 0701, с ребенком до 3 лет",
                "proc": "rep_dia_0701_03",
                "data_approve": "14.02.2023",
                "author": "Гусейнов Ш.",
                "params": {"date_first": "C", "date_second": "по"},
            },
            "04": {
                "name": "Списочный состав получателей 0701, с иждивенцем старше 18 лет",
                "proc": "rep_dia_0701_04",
                "data_approve": "14.02.2023",
                "author": "Гусейнов Ш.",
                "params": {"date_first": "C", "date_second": "по "},
            },
            "05": {
                "name": "Получатели СВут 0702 за период (месяц)",
                "proc": "rep_dia_0702_01",
                "data_approve": "14.02.2023",
                "author": "Гусейнов Ш.",
                "params": {"date_first": "На"},
            },
        },
        "320": {
            "01": {
                "name": "Сведения о численности получателей и сумм их выплат",
                "proc": "rep_dia_320_01",
                "data_approve": "13.06.2023",
                "author": "Адильханова А.К.",
                "params": {"date_first": "На"},
                },
            },
    },
    "Актуарии": {
        "1500": {
            "live_time": "1",
            "module_dir": f"{REPORT_MODULE_PATH}.AKTUAR",
            "01": {
                "name": "Получатели СВут 0702 за период",
                "proc": "rep_dia_0702_01",
                "data_approve": "24.02.2023",
                "author": "Гусейнов Ш.",
                "params": {"srfpm_id": "Код выплаты:4", "date_first": "Месяц расчета"},
            },
            "02": {
                "name": "Получатели СВпт 0703 за период",
                "proc": "rep_dia_0702_01",
                "data_approve": "24.02.2023",
                "author": "Гусейнов Ш.",
                "params": {"srfpm_id": "Код выплаты:4", "date_first": "Месяц расчета"},
            },
        }
    },
}