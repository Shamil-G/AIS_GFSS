create table a_temp_16_01_2023
as
-- select count(sicid) cnt,
--        sum(phys),
--        sum(uric),
--        sum(smesh_uric_1),
--        sum(smesh_uric_2)
-- from (       
    select sicid, 
           case when phys>0 and uric=0 then 1 else 0 end phys,
           case when phys=0 and uric>0 then 1 else 0 end uric,
           case when phys>0 and uric>0 then 1 else 0 end smesh_uric_1,
           case when phys=0 and uric=0 then 1 else 0 end smesh_uric_2
    from (         
        select sicid, sum(phys) phys, sum(uric) uric
        from (
            select si.sicid, si.mhmh_id,
                 case when si.p_rnn=p.rn then 1 else 0 end phys,
                 case when si.p_rnn!=p.rn then 1 else 0 end uric
            from si_member_2 si, person p
            where si.type_payer not in ('Ş', 'Å')
--            and si.sicid in (27258826, 24606604, 25589062)    
            and si.pay_date between '01.01.2022' and '31.12.2022'
            and   si.sicid=p.sicid
        )    
        group by sicid
    )
-- )


create table a_temp_16_01_2023_esp
as
-- select count(sicid) cnt,
--        sum(phys),
--        sum(uric),
--        sum(smesh_uric_1),
--        sum(smesh_uric_2)
-- from (       
    select sicid, 
           case when phys>0 and uric=0 then 1 else 0 end phys,
           case when phys=0 and uric>0 then 1 else 0 end uric,
           case when phys>0 and uric>0 then 1 else 0 end smesh_uric_1,
           case when phys=0 and uric=0 then 1 else 0 end smesh_uric_2
    from (         
        select sicid, sum(phys) phys, sum(uric) uric
        from (
            select si.sicid, si.mhmh_id,
                 case when si.p_rnn=p.rn then 1 else 0 end phys,
                 case when si.p_rnn!=p.rn then 1 else 0 end uric
            from si_member_2 si, person p
            where si.type_payer not in ('Ş')
            and si.type_payer = 'Å'
--            and si.sicid in (27258826, 24606604, 25589062)    
            and si.pay_date between '01.01.2022' and '31.12.2022'
            and   si.sicid=p.sicid
        )    
        group by sicid
    )
-- )


select sum(a.phys) cnt_phys,
       sum(a.uric) cnt_uric,
       sum(a.smesh_uric_1) cnt_smesh_uric_1,
       sum(a.smesh_uric_2) cnt_smesh_uric_2
from a_temp_16_01_2023 a 
--where cnt is not null
union
select sum(a.phys) cnt_phys,
       sum(a.uric) cnt_uric,
       sum(a.smesh_uric_1) cnt_smesh_uric_1,
       sum(a.smesh_uric_2) cnt_smesh_uric_2
from a_temp_16_01_2023_esp a 




declare
 cnt pls_integer default 0;
begin
          for cur in (select pd.pncd_id, pd.rfpm_id, count(pd.rfpm_id) as cnt 
                      from pnpd_document pd, a_temp_16_01_2023 a
                      where pncp_date between '01.01.2022' and '31.12.2022'
                      and   a.sicid=pd.pncd_id
                      group by pd.pncd_id, pd.rfpm_id
          )
          loop
             update a_temp_16_01_2023 a
             set a.rfpm_id=cur.rfpm_id,
                 a.cnt=cur.cnt
             where a.sicid=cur.pncd_id;
             if cnt > 999 then
                cnt:=0;
                commit;
             end if;
             cnt:=cnt+1; 
          end loop;
          commit;
end;          


declare
 cnt pls_integer default 0;
begin
          for cur in (select pd.pncd_id, pd.rfpm_id, count(pd.rfpm_id) as cnt 
                      from pnpd_document pd, a_temp_16_01_2023_esp a
                      where pncp_date between '01.01.2022' and '31.12.2022'
                      and   a.sicid=pd.pncd_id
                      group by pd.pncd_id, pd.rfpm_id
          )
          loop
             update a_temp_16_01_2023_esp a
             set a.rfpm_id=cur.rfpm_id,
                 a.cnt=cur.cnt
             where a.sicid=cur.pncd_id;
             if cnt > 999 then
                cnt:=0;
                commit;
             end if;
             cnt:=cnt+1; 
          end loop;
          commit;
end;  
