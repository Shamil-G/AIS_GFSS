create or replace package UTIL is

  -- Author  : ГУСЕЙНОВ_Ш
  -- Created : 28.06.2019 15:34:24
  -- Purpose : Небольшие общие процедуры

  debug_level      number default 1;
  procedure log(iobj in varchar, iaction in varchar2, ierror in nvarchar2);


  function locked return SYS_REFCURSOR;
  procedure index_on(itable_name varchar2);

end UTIL;
/
create or replace package body UTIL is

  e_errm           varchar2(1024);

  --procedure log(iobj in varchar, iaction in varchar2, ierror in nvarchar2 := '');

  procedure log(iobj in varchar, iaction in varchar2, ierror in nvarchar2)
  is
  PRAGMA AUTONOMOUS_TRANSACTION;
  begin
    insert into log values(CURRENT_TIMESTAMP, iobj, iaction, ierror);
    commit;
  end log;

  function locked return SYS_REFCURSOR
  is
     ret_cursor SYS_REFCURSOR;
  begin
   open ret_cursor for '
        select
           c.owner,
           c.object_name,
           c.object_type,
           b.sid,
           b.serial#,
           b.status,
           b.osuser,
           b.machine
        from
           v$locked_object a,
           v$session b,
           dba_objects c
        where
           b.sid = a.session_id
        and
           a.object_id = c.object_id
   ';
   return ret_cursor;
  end;


  procedure index_on(itable_name varchar2)
  is
    v_count_ins pls_integer default 0;
  begin
    log(itable_name, 'Начинаем перестройку индексов', '');
    dbms_application_info.set_module('LOAD_TABLE->BUILD INDEX', itable_name);

    FOR current_index IN
    (
        select * from
        (
          SELECT 'ALTER INDEX '||INDEX_NAME||' REBUILD ONLINE PARALLEL' build_command, ui.index_name index_name, uniqueness
            FROM    user_indexes ui
            WHERE table_owner='SSWH'
            and table_name = itable_name
            and status = 'UNUSABLE'
            and partitioned='NO'
          UNION ALL
          SELECT 'ALTER INDEX '||index_name||' REBUILD PARTITION '||partition_name||' ONLINE PARALLEL', uip.index_name, 'partition' uniqueness
            FROM    user_ind_PARTITIONS uip
            WHERE   status = 'UNUSABLE'
            and   index_name in (select index_name from all_indexes where table_name = itable_name)
          UNION ALL
          SELECT 'ALTER INDEX '||index_name||' REBUILD SUBPARTITION '||subpartition_name||' ONLINE PARALLEL', uis.index_name, 'subpartition' uniqueness
            FROM    user_ind_SUBPARTITIONS uis
            WHERE   status = 'UNUSABLE'
            and   index_name in (select index_name from all_indexes where table_name = itable_name)
        ) order by uniqueness desc, build_command
    )
    LOOP
      begin
        log(itable_name, 'Перестраиваем индекс '||current_index.index_name,current_index.build_command);
        EXECUTE immediate current_index.build_command;
      exception when others then
                e_errm:=sqlerrm;
                log(itable_name, 'Ошибка перестройки индекса: '||current_index.build_command, e_errm);
      end;
    END LOOP;


    --  Гусейнов Ш.А. 10.02.2020
    if v_count_ins < 2048 then
        for current_constraint in (
                  select 'ALTER TABLE '||table_name||' ENABLE CONSTRAINT '||a.CONSTRAINT_NAME command
                  from user_constraints a
                  where table_name = itable_name
                  and status = 'DISABLED'
                  )
        loop
          log(itable_name, 'Включаем PRIMARY KEY',current_constraint.command);
          EXECUTE immediate current_constraint.command;
        end loop;
    end if;
    --*/

    log(itable_name,'Перестройка индексов завершена','');
  end index_on;

begin
  debug_level:=3;
end UTIL;
/
