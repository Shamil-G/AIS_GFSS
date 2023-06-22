from app_config import REPORT_MODULE_PATH

# live_time - время жизни отчета в часах, может указываться с 2 занками после запятой
# в этом случае время минимальное жизни отчета составляет 36 секунд


dict_reports = {
    "ДИА": 
    [
        {
            "grp_name": "1501", 
            "module_dir": f"{REPORT_MODULE_PATH}.DIA.1501",
            "live_time": "0",
            "list": 
            [
                {
                    "name": "Количество иждивенцев и сумма 0701 за период",
                    "num_rep": "01",
                    "proc": "rep_0701_01",
                    "data_approve": "13.02.2023",
                    "author": "Гусейнов Ш.",
                    "params": {"date_first": "C", "date_second": "по"},
                },
                {
                    "name": "Списочный состав иждивенцев",
                    "num_rep": "02",
                    "proc": "rep_0701_02",
                    "data_approve": "14.02.2023",
                    "author": "Гусейнов Ш.",
                    "params": {"date_first": "C", "date_second": "по"},
                },
                {
                    "name": "Списочный состав получателей 0701, с ребенком до 3 лет",
                    "num_rep": "03",
                    "proc": "rep_0701_03",
                    "data_approve": "14.02.2023",
                    "author": "Гусейнов Ш.",
                    "params": {"date_first": "C", "date_second": "по"},
                },
                {
                    "name": "Списочный состав получателей 0701, с иждивенцем старше 18 лет",
                    "num_rep": "04",
                    "proc": "rep_0701_04",
                    "data_approve": "14.02.2023",
                    "author": "Гусейнов Ш.",
                    "params": {"date_first": "C", "date_second": "по "},
                }
            ]
        },
        {
            "grp_name": "1502", 
            "module_dir": f"{REPORT_MODULE_PATH}.DIA.1502",
            "live_time": "0",
            "list": 
            [
                {
                    "name": "Получатели СВут 0702 за период (месяц)",
                    "num_rep": "01",
                    "proc": "rep_0702_01",
                    "data_approve": "14.02.2023",
                    "author": "Гусейнов Ш.",
                    "params": {"date_first": "На"},
                }
            ]
        },
        {
            "grp_name": "1503", 
            "module_dir": f"{REPORT_MODULE_PATH}.DIA.1503",
            "live_time": "0",
            "list": 
            [
                {
                    "name": "СО после окончания СВпр, в градации по месяцам после даты окончания выплаты",
                    "num_rep": "01",
                    "proc": "rep_0703_01",
                    "data_approve": "22.06.2023",
                    "author": "Гусейнов Ш.",
                    "params": {"date_first": "На"},
                }
            ]
        },
        { 
            "grp_name": "300", 
            "module_dir": f"{REPORT_MODULE_PATH}.DIA.300",
            "live_time": "1",
            "list": 
            [
                {
                "name": "Сведения о поступивших возвратах излишне зачисленных (выплаченных) сумм социальных выплат. Отчет 9V для Министерства",
                "num_rep": "09",
                "proc": "rep_dia_300_09",
                "data_approve": "13.06.2023",
                "author": "Гусейнов Ш.А.",
                "params": {"date_first": "C", "date_second": "по "},
                }
            ]
        },
        {
            "grp_name": "320", 
            "module_dir": f"{REPORT_MODULE_PATH}.DIA.320",
            "live_time": "1",
            "list": 
            [
                {
                    "name": "Сведения о численности получателей и сумм их выплат - в разработке Адильхановой!!!",
                    "num_rep": "09",
                    "proc": "rep_dia_320_01",
                    "data_approve": "13.06.2023",
                    "author": "Адильханова А.К.",
                    "params": {"date_first": "На"},
                }
            ]
        }
    ]
    ,
    "Актуар":
    [
        {
            "grp_name": "1500",
            "live_time": "1",
            "module_dir": f"{REPORT_MODULE_PATH}.AKTUAR",
            "list": [
                {
                    "name": "Получатели СВут 0702 за период",
                    "num_rep": "01",
                    "proc": "rep_dia_0702_01",
                    "data_approve": "24.02.2023",
                    "author": "Гусейнов Ш.",
                    "params": {"srfpm_id": "Код выплаты:4", "date_first": "Месяц расчета"},
                },
                {
                    "name": "Получатели СВпт 0703 за период",
                    "num_rep": "02",
                    "proc": "rep_dia_0702_01",
                    "data_approve": "24.02.2023",
                    "author": "Гусейнов Ш.",
                    "params": {"srfpm_id": "Код выплаты:4", "date_first": "Месяц расчета"},
                }
            ]
        }
    ]
}