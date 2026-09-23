import pandas as pd, numpy as np
NA=np.nan
ETR_Q1FY27="https://b.zmtcdn.com/investor-relations/Eternal_Limited_Shareholders_Letter_Q1FY27_Results.pdf"
ETR_Q4FY25="https://b.zmtcdn.com/investor-relations/d9c290cd23764a09789769c39682276a_1746094084.pdf"
ETR_Q3FY25="https://b.zmtcdn.com/investor-relations/681c57ac651e6e8f54c263ffbfc1e0b9_1737369246.pdf"
SWG_Q1FY27="https://www.swiggy.com/corporate/wp-content/uploads/2026/07/Q1-FY2027-Shareholder-letter.pdf"
SWG_Q4FY26="https://www.swiggy.com/corporate/wp-content/uploads/2026/05/Q4-FY2026-Shareholder-letter.pdf"
SWG_Q2FY26="https://www.swiggy.com/corporate/wp-content/uploads/2025/10/Q2-FY2026-Shareholder-letter.pdf"
SWG_Q1FY26="https://www.swiggy.com/corporate/wp-content/uploads/2025/07/Q1-FY2026-Shareholder-letter.pdf"
qs=["Q4FY24","Q1FY25","Q2FY25","Q3FY25","Q4FY25","Q1FY26","Q2FY26","Q3FY26","Q4FY26","Q1FY27"]
qend=dict(zip(qs,pd.to_datetime(["2024-03-31","2024-06-30","2024-09-30","2024-12-31","2025-03-31","2025-06-30","2025-09-30","2025-12-31","2026-03-31","2026-06-30"])))
# ---------------- Blinkit (Eternal) ----------------
b=pd.DataFrame({
 "quarter":qs,
 "gov_cr":[4027,4923,6132,7798,9421,NA,NA,NA,NA,NA],
 "nov_cr":[3336,4061,4928,6020,7362,9203,11679,13300,14386,17132],
 "revenue_cr":[769,942,1156,1399,1709,2400,9891,12256,13232,15664],
 "contribution_cr":[158,199,234,232,289,360,542,736,782,907],
 "adj_ebitda_cr":[-37,-3,-8,-103,-178,-162,-156,4,37,102],
 "orders_mn":[NA,NA,NA,NA,NA,176.7,222.7,243.3,273.9,331.0],
 "mtu_mn":[NA,NA,NA,NA,NA,16.9,20.8,23.6,27.2,31.8],
 "stores_end":[526,639,791,1007,1301,1544,1816,2027,2243,2443],
 "nov_per_store_day_k":[NA,NA,NA,NA,NA,734,771,750,768,827],
 "cm_pct_gov":[NA]*10,
})
b["platform"]="Blinkit"
b["source"]=[ETR_Q4FY25]*5+[ETR_Q1FY27]*5
b["notes"]=["stores: Eternal company overview (FY24 526)"]+["stores derived from Q3FY25 letter (1,007 less 216 / 152 net adds)"]*2+["stores: Q3FY25 letter"]+["stores: FY25 1,301 (Eternal company overview Jul-2025)"]+ \
 ["Revenue jumps from Q2FY26: shift to inventory-led (1P) model, revenue now includes goods sold; orders include cancelled orders"]*5
# ---------------- Instamart (Swiggy) ----------------
iq=qs[1:]
orders=[56,68,73,88.6,92.4,100.8,106.4,112.6,114.5]
aov=[487,499,534,527,612,697,746,700,691]
novpct=[.88,.85,.79,.76,.74,.70,.69,.72,.74]
gov_rep={"Q1FY26":5655,"Q4FY26":7881,"Q1FY27":7907}
nov_rep={"Q4FY26":5675,"Q1FY27":5817}
gov=[gov_rep.get(q, round(o*a/10,0)) for q,o,a in zip(iq,orders,aov)]  # orders mn * INR /10 = INR cr
nov=[nov_rep.get(q, round(g*p,0)) for q,g,p in zip(iq,gov,novpct)]
i=pd.DataFrame({
 "quarter":iq,"gov_cr":gov,"nov_cr":nov,"revenue_cr":[NA]*9,
 "cm_pct_gov":[NA,NA,NA,-5.6,-4.6,-2.6,-2.45,-1.8,-0.2],
 "adj_ebitda_cr":[-318,-359,-578,-840,-896,-849,-908,-858,-778],
 "orders_mn":orders,"aov_inr":aov,"nov_pct_gov":novpct,
 "mtu_mn":[5.2,6.2,7.0,9.8,11.1,12.0,12.8,13.3,13.5],
 "stores_end":[557,609,705,1021,1062,1102,1136,1143,1171],
 "orders_per_store_day":[1144,1260,1236,1190,985,1025,1034,1093,1089],
 "store_area_mn_sqft":[NA,NA,NA,NA,4.30,4.59,4.79,4.81,4.92],
 "gov_per_sqft_inr":[16402,17359,15946,11762,13163,15287,16571,16391,16056],
})
i["contribution_cr"]=(i.cm_pct_gov/100*i.gov_cr).round(0)
i["platform"]="Instamart"
i["source"]=[SWG_Q1FY26]*4+[SWG_Q1FY27]*5
i["notes"]=["GOV = orders x AOV (derived); NOV = GOV x NOV% (derived); CM% not comparable pre-Q4FY25"]*3+ \
 ["CM% -5.6 peak (Q1FY27 letter Q6); GOV/NOV derived"]+["GOV reported 5,655; CM -4.6%; NOV derived"]+["CM -2.6% (Q2FY26 letter); GOV/NOV derived"]+ \
 ["CM derived: Q4FY26 -1.8% was a 65bps QoQ improvement; GOV/NOV derived"]+["GOV 7,881 & NOV 5,675 reported (Q4FY26 letter)"]+["GOV 7,907 & NOV 5,817 reported; CM -0.2%"]
panel=pd.concat([b,i],ignore_index=True)
panel["period_end"]=panel.quarter.map(qend)
cols=["platform","quarter","period_end","gov_cr","nov_cr","revenue_cr","contribution_cr","cm_pct_gov","adj_ebitda_cr","orders_mn","aov_inr","nov_pct_gov","mtu_mn","stores_end","nov_per_store_day_k","orders_per_store_day","store_area_mn_sqft","gov_per_sqft_inr","source","notes"]
panel=panel[cols]
panel.to_csv("./data/qcom_quarterly_panel.csv",index=False)
# ---------------- Zepto annual ----------------
ENT="https://entrackr.com/fintrackr/zepto-doubles-revenue-in-fy26-losses-widen-to-rs-5905-cr-12016560"
OLB="https://www.outlookbusiness.com/start-up/how-far-zepto-fell-short-of-its-breakeven-goals"
z=pd.DataFrame({"platform":["Zepto","Zepto"],"fiscal_year":["FY25","FY26"],
 "revenue_cr":[11110,22624],"net_loss_cr":[4700,5905],
 "adj_ebitda_cr":[round(-5041.5/1.115,0),-5041.5],
 "adj_ebitda_per_order_inr":[-136.15,-78.75],
 "ad_revenue_cr":[round(1636/2.5,0),1636],
 "operating_cash_flow_cr":[-4625,-3462],
 "stores_end":[NA,1139],"orders_per_day_exit_mn":[NA,1.75],
 "source":[OLB+" ; "+ENT]*2,
 "notes":["adj EBITDA derived from FY26 figure being +11.5% YoY; ad revenue derived from '2.5X' growth","Adj EBITDA -19.5% of NRV (Q1FY26) -> -15.3% (Q4FY26); UDRHP filed Jun-2026"]})
z["orders_mn_derived"]=(z.adj_ebitda_cr*1e7/z.adj_ebitda_per_order_inr/1e6).round(0)
z.to_csv("./data/zepto_annual.csv",index=False)
# ---------------- Management guidance / frameworks ----------------
g=pd.DataFrame([
 ["Blinkit","capex_per_store_cr",2.5,"Steady-state capex per store incl. warehousing",ETR_Q1FY27],
 ["Blinkit","nov_per_store_day_lakh",11,"Steady-state NOV per store per day",ETR_Q1FY27],
 ["Blinkit","nwc_days_of_nov",12,"Net working capital, days of NOV",ETR_Q1FY27],
 ["Blinkit","adj_ebitda_pct_nov",6,"Steady-state Adj. EBITDA margin",ETR_Q1FY27],
 ["Blinkit","ebit_pct_nov",4,"Steady-state EBIT margin",ETR_Q1FY27],
 ["Blinkit","inventory_loss_pct_nov",1.8,"Current inventory losses (expiry, shrinkage, damage)",ETR_Q1FY27],
 ["Blinkit","nwc_cr_q1fy27",2545,"Net working capital end Q1FY27",ETR_Q1FY27],
 ["Instamart","breakeven_nov_runrate_cr",60000,"Annualised NOV run-rate for Adj. EBITDA breakeven",SWG_Q1FY27],
 ["Instamart","breakeven_cm_pct",5.5,"CM needed at breakeven (5-6% guided; midpoint)",SWG_Q1FY27],
 ["Instamart","breakeven_cm_per_order_inr",30,"~INR 30 CM per order needed",SWG_Q1FY27],
 ["Instamart","lever_mix_margin_inr",10,"Higher margin & product mix, INR/order",SWG_Q1FY27],
 ["Instamart","lever_ads_inr",10,"Ad revenue, INR/order",SWG_Q1FY27],
 ["Instamart","lever_automation_inr",5,"Densification & automation, INR/order",SWG_Q1FY27],
 ["Instamart","lever_op_leverage_inr",5,"Operating leverage, INR/order",SWG_Q1FY27],
 ["Instamart","lever_inventory_model_inr",4.5,"Inventory-led (IOCC) model, INR/order (4-5 guided)",SWG_Q1FY27],
 ["Instamart","store_utilisation_pct",40,"Current store utilisation (~40%)",SWG_Q1FY27],
 ["Instamart","m1_retention_pct_q1fy27",61,"1-month retention of transacting users (vs 55% in Q1FY26)",SWG_Q1FY27],
 ["Instamart","stores_cm_positive_pct",45,">45% of stores CM positive (30% prior quarter)",SWG_Q1FY27],
 ["Instamart","maxxsaver_mtu_adoption_pct",28,"Share of MTUs who used Maxxsaver in its launch quarter (Q1FY26)",SWG_Q1FY26],
],columns=["platform","metric","value","description","source"])
g.to_csv("./data/management_guidance.csv",index=False)
print(panel[["platform","quarter","gov_cr","nov_cr","contribution_cr","adj_ebitda_cr","orders_mn","stores_end"]].to_string())
print(z.T)
