from app_config import REPORT_MODULE_PATH
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
                },
                {
                    "name": "Списки умерших кормильцев по действующим СВ",
                    "num_rep": "05",
                    "proc": "rep_0701_05",
                    "data_approve": "27.09.2023",
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
                    "name": "Получатели СВут 0702 за месяц",
                    "num_rep": "01",
                    "proc": "rep_0702_01",
                    "data_approve": "14.02.2023",
                    "author": "Гусейнов Ш.",
                    "params": {"date_first": "На"},
                },
                {
                    "name": "Получатели СВут 0702 за период",
                    "num_rep": "02",
                    "proc": "rep_0702_02",
                    "data_approve": "21.09.2023",
                    "author": "Гусейнов Ш.",
                    "params": {"date_first": "C", "date_second": "по"},
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
                },
                {
                    "name": "Получатели СВпр, выплата которым назначена в тот же месяц, что и месяц окончания СВпр",
                    "num_rep": "02",
                    "proc": "rep_0703_02",
                    "data_approve": "23.06.2023",
                    "author": "Гусейнов Ш.",
                    "params": {"date_first": "Выберите месяц: "},
                },
                {
                    "name": "Получатели СВпр за период",
                    "num_rep": "03",
                    "proc": "rep_0703_03",
                    "data_approve": "22.09.2023",
                    "author": "Гусейнов Ш.",
                    "params": {"date_first": "C", "date_second": "по"},
                }
            ]
        },
        {
            "grp_name": "1504", 
            "module_dir": f"{REPORT_MODULE_PATH}.DIA.1504",
            "live_time": "0",
            "list": 
            [
                {
                    "name": "Получатели СВбр и СВур, у которых между датами назначения есть СВпр",
                    "num_rep": "01",
                    "proc": "rep_0704_01",
                    "data_approve": "30.06.2023",
                    "author": "Гусейнов Ш.",
                    "params": {"date_first": "На"},
                },
                {
                    "name": "Получатели СВбр за период",
                    "num_rep": "02",
                    "proc": "rep_0704_02",
                    "data_approve": "28.09.2023",
                    "author": "Гусейнов Ш.",
                    "params": {"date_first": "C", "date_second": "по"},
                }
            ]
        },
        {
            "grp_name": "1505", 
            "module_dir": f"{REPORT_MODULE_PATH}.DIA.1505",
            "live_time": "0",
            "list": 
            [
                {
                    "name": "Получатели СВур",
                    "num_rep": "01",
                    "proc": "rep_0705_01",
                    "data_approve": "30.06.2023",
                    "author": "Гусейнов Ш.",
                    "params": {"date_first": "C", "date_second": "по"},
                },
            ]
        },
        { 
            "grp_name": "300", 
            "module_dir": f"{REPORT_MODULE_PATH}.DIA.300",
            "live_time": "0",
            "list": 
            [
                {
                "name": "Сведения о поступивших возвратах излишне зачисленных (выплаченных) сумм социальных выплат. Отчет 9V для Министерства",
                "num_rep": "01",
                "proc": "rep_dia_300_09",
                "data_approve": "13.06.2023",
                "author": "Гусейнов Ш.А.",
                "params": {"date_first": "C", "date_second": "по "},
                },
                {
                    "name": "Список плательщиков, уплативших социальные отчисления за работников с численностью более 50 человек хотя бы 1 раз за предыдущие 6 месяцев",
                    "num_rep": "02",
                    "proc": "rep_dia_50",
                    "data_approve": "26.07.2023",
                    "author": "Алиманов Д.Д.",
                    "params": {"date_first": "С", "date_second": "по"},
                }
            ]
        },
        { 
            "grp_name": "6020", 
            "module_dir": f"{REPORT_MODULE_PATH}.DIA.6020",
            "live_time": "0",
            "list": 
            [
                {
                "name": "Список лиц, которым назначена социальная выплата на случай потери кормильца",
                "num_rep": "01",
                "proc": "rep_dia_6021",
                "data_approve": "14.09.2023",
                "author": "Алиманов Д.Д.",
                "params": {"date_first": "C", "date_second": "по "},
                },
                {
                "name": "Список лиц, которым назначена социальная выплата на случай утраты трудоспособности",
                "num_rep": "02",
                "proc": "rep_dia_6022",
                "data_approve": "14.09.2023",
                "author": "Алиманов Д.Д.",
                "params": {"date_first": "C", "date_second": "по "},
                },
                 {
                "name": "Список лиц, которым назначена социальная выплата на случай потери работы",
                "num_rep": "03",
                "proc": "rep_dia_6023",
                "data_approve": "14.09.2023",
                "author": "Алиманов Д.Д.",
                "params": {"date_first": "C", "date_second": "по "},
                },
                 {
                "name": "Список лиц, которым назначена социальная выплата на случай потери дохода в связи с беременностью и родами, усыновлением/удочерением ребенка",
                "num_rep": "04",
                "proc": "rep_dia_6024",
                "data_approve": "14.09.2023",
                "author": "Алиманов Д.Д.",
                "params": {"date_first": "C", "date_second": "по "},
                },
                 {
                "name": "Список лиц, которым назначена социальная выплата на случай потери дохода в связи с уходом за ребенком по достижении им возраста 1 года",
                "num_rep": "05",
                "proc": "rep_dia_6025",
                "data_approve": "14.09.2023",
                "author": "Алиманов Д.Д.",
                "params": {"date_first": "C", "date_second": "по "},
                }

            ]
        },
        {
            "grp_name": "ЕдПлатеж", 
            "module_dir": f"{REPORT_MODULE_PATH}.DIA.cp",
            "live_time": "0",
            "list": 
            [
                {
                    "name": "Сведения о численности получателей и сумм их выплат (made by Адильханова)",
                    "num_rep": "01",
                    "proc": "rep_dia_cp_01",
                    "data_approve": "12.07.2023",
                    "author": "Адильханова А.К.",
                    "params": {"date_first": "С", "date_second": "по"},
                },
                {
                "name": "Участники ЕП, в разрезе пола и возраста",
                "num_rep": "02",
                "proc": "rep_dia_cp_02",
                "data_approve": "10.06.2023",
                "author": "Адильханова А.К.",
                "params": {"date_first": "C", "date_second": "по", "srfbn_id": "Код региона:2"},
                },
                {
                "name": "Участники ЕП, в разрезе регионов",
                "num_rep": "03",
                "proc": "rep_dia_cp_03",
                "data_approve": "12.09.2023",
                "author": "Гусейнов Ш.А.",
                "params": {"date_first": "C", "date_second": "по"},
                }
            ]
        },
        {
            "grp_name": "ЕСП", 
            "module_dir": f"{REPORT_MODULE_PATH}.DIA.esp",
            "live_time": "0",
            "list": 
            [
                {
                    "name": "Списочная часть чистых ЕСП-шников",
                    "num_rep": "01",
                    "proc": "rep_dia_esp_01",
                    "data_approve": "25.07.2023",
                    "author": "Алиманов Д.Д.",
                    "params": {"date_first": "С", "date_second": "по"},
                },
                {
                    "name": "Списочная часть смешанных ЕСП-шников",
                    "num_rep": "02",
                    "proc": "rep_dia_esp_02",
                    "data_approve": "25.07.2023",
                    "author": "Алиманов Д.Д.",
                    "params": {"date_first": "С", "date_second": "по"},
                },
                {
                    "name": "Списочная часть смешанных ЕСП-шников(СВ)",
                    "num_rep": "03",
                    "proc": "rep_dia_esp_03_sv",
                    "data_approve": "14.09.2023",
                    "author": "Алиманов Д.Д.",
                    "params": {"date_first": "С", "date_second": "по"},
                },
                {
                    "name": "Списочная часть чистых ЕСП-шников(СВ)",
                    "num_rep": "04",
                    "proc": "rep_dia_esp_04_sv",
                    "data_approve": "14.09.2023",
                    "author": "Алиманов Д.Д.",
                    "params": {"date_first": "С", "date_second": "по"},
                }
            ]
        },
        {
            "grp_name": "минСО", 
            "module_dir": f"{REPORT_MODULE_PATH}.DIA.minCO",
            "live_time": "0",
            "list": 
            [
                {
                    "name": "Списочная часть по социальным отчислениям, меньшим установленного минимального уровня",
                    "num_rep": "01",
                    "proc": "rep_dia_co_01",
                    "data_approve": "14.07.2023",
                    "author": "Гусейнов Ш.А.",
                    "params": {"date_first": "Период:"}
                }
            ]
        }

    ]
    ,
    "ДСР":
    [
        {
            "grp_name": "Выплаты",
            "live_time": "100",
            "module_dir": f"{REPORT_MODULE_PATH}.DSR",
            "list": [
                {
                    "name": "Контроль сроков по выплатам",
                    "num_rep": "01",
                    "proc": "dsr_01",
                    "data_approve": "11.10.2023",
                    "author": "Гусейнов Ш.",
                    "params": {"srfpm_id": "Код выплаты:4", "date_first": "С", "date_second": "по"},
                },
            ]
        }
    ]
    ,
}