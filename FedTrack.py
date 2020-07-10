import bs4 as bs
import datetime as dt
import matplotlib.pyplot as plt
from matplotlib import style
import numpy as np
import pandas as pd
import pandas_datareader as web
import requests
import time

style.use("ggplot")
pd.set_option('display.max_columns', 100)
pd.set_option('display.width', 1000)

# Main website we will be pulling information from.
fed_url = 'https://www.federalreserve.gov/publications/reports-to-congress-in-response-to-covid-19.htm'

# Lending facilities we'll be tracking. Note that hrefs are partial for date flexibility.
pdcf_title = 'Primary Dealer Credit Facility' # Not yet operational

cpff_title = 'Commercial Paper Funding Facility' # Not yet operational

mmmflf_title = 'Money Market Mutual Fund Liquidity Facility' # Not yet operational

tabslf_title = 'Term Asset-Backed Securities Loan Facility' # Not yet operational

smccf_title = 'Secondary Market Corporate Credit Facility'
smccf_href = '/publications/files/smccf-transition-specific-disclosures-'
pmccf_title = 'Primary Market Corporate Credit Facility'
smccf_pmccf_allocation = 750000000000

mlf_title = 'Municipal Liquidity Facility'
mlf_href = '/publications/files/MLF-transaction-specific-disclosures-'
mlf_allocation = 500000000000

ppplf_title = 'Paycheck Protection Program Liquidity Facility'
ppplf_href = '/publications/files/PPPLF-transaction-specific-disclosures-'
ppp_allocation = 669000000000

mself_title = 'Main Street Expanded Loan Facility' # Not yet operational


msnlf_title = 'Main Street New Loan Facility' # Not yet operational


msplf_title = 'Main Street Priority Loan Facility' # Not yet operational
    

def sp500_tickers():
    resp = requests.get("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")
    soup = bs.BeautifulSoup(resp.text, "lxml")
    table = soup.find("table", {"class": "wikitable sortable"})
    tickers = []
    for row in table.findAll("tr")[1:]:
        ticker = row.findAll("td")[0].text
        ticker = ticker.replace("\n", "")
        tickers.append(ticker)

    companies = []
    for row in table.findAll("tr")[1:]:
        company = row.findAll("td")[1].text
        company = company.replace("\n", "")
        companies.append(company)

    raw_data = {'Ticker': tickers, 'Issuer': companies} 
    df_tickers = pd.DataFrame(raw_data, columns=['Ticker','Issuer'])
    df_tickers['Issuer'] = df_tickers['Issuer'].apply(lambda x: x.upper())
    # reps = {'&': '', r'[^\w\s]': '', ' INC': '', ' PLC': '', ' CO': ' COMPANY'}
    reps_remove = {'&', r'[^\w\s]', ' INC', ' PLC'}
    for rep in reps_remove:
        df_tickers['Issuer'] = df_tickers['Issuer'].str.replace(rep, '')

    return df_tickers

df_tickers = sp500_tickers()

# SMCCF, MLF, and PPPLF are frequently updated with transaction-specific disclosures. Thus, we will be focusing on these first, in the listed order.

# SMCCF
# def smccf_data():
#     resp = requests.get(fed_url)
#     soup = bs.BeautifulSoup(resp.text, "lxml")


# SMCCF raw data sheet has 6 tabs. We care about 4 tabs: the current bond position summary, sector breakdown, credit breakdown, and current ETF position summary. See commented out code above for requests/bs4 pull when we decide to make the excel pull dynamic.
smccf_excel = 'smccf-6-28-20.xlsx'

# Cleaned current bond position summary (using amortized cost, not par value). Care about: number of issuers represented in the dataset, total amortized cost, and % of total allocation.
df_bond = pd.read_excel(open(smccf_excel,'rb'), sheet_name='Position Summary-Bond')
df_bond.drop(df_bond.columns[[2, 3, 5]], axis=1, inplace=True)
df_bond = df_bond[:-2]
df_bond['% of Program Allocation'] = df_bond.iloc[:,3] / smccf_pmccf_allocation

df_bond_issuers = df_bond['Issuer'].groupby(df_bond.iloc[:,0]).nunique().count()
df_bond_cost = sum(df_bond.iloc[:,3])
df_bond_cost_str = '${:,.2f}'.format(df_bond_cost)
df_bond_allocation = '{:.2%}'.format(sum(df_bond.iloc[:,4]))

print("SMCCF: " + df_bond_cost_str + " Invested in " + str(df_bond_issuers) + " Issuers")
print("SMCCF: " + str(df_bond_allocation) + " of PMCCF/SMCCF Allocation Invested in Individual Bonds")


# Cleaned current bond position sector exposure as a % of total cost. Care about: sector composition.
df_bond_sectors = pd.read_excel(open(smccf_excel,'rb'), sheet_name='Sector Summary-Bond')
df_bond_sectors.drop(df_bond_sectors.columns[[1, 2]], axis=1, inplace=True)
df_bond_sectors = df_bond_sectors[:-3]

sector_data = df_bond_sectors.iloc[:,1]
sector_labels = df_bond_sectors.iloc[:,0]

fig1, ax1 = plt.subplots()
ax1.pie(sector_data, labels=sector_labels, autopct='%.1f%%', labeldistance=1.1, pctdistance=0.9, startangle=90)
ax1.axis('equal')
plt.title("SMCCF Sector Composition", pad=25)

# plt.show()


# Cleaned current bond position credit exposure.
df_bond_credit = pd.read_excel(open(smccf_excel,'rb'), sheet_name='Rating&WAM-Bond')
df_bond_credit.drop(df_bond_credit.columns[3:], axis=1, inplace=True)
df_bond_credit.drop(df_bond_credit.index[0], inplace=True)
df_bond_credit = df_bond_credit[:-5] # Includes removing WAM

credit_data = df_bond_credit.iloc[:,1]
credit_labels = df_bond_credit.iloc[:,0]

fig2, ax1 = plt.subplots()
ax1.pie(credit_data, labels=credit_labels, autopct='%.1f%%', labeldistance=1.1, pctdistance=0.8, startangle=90)
ax1.axis('equal')
plt.title("SMCCF Credit Composition", pad=25)

plt.show()


# Cleaned current ETF position summary. Care about: number of funds represented in the dataset, total market value (best proxy for cost at this time), and % of total allocation.
df_etf = pd.read_excel(open(smccf_excel,'rb'), sheet_name='Position Summary-ETF')
df_etf = df_etf[:-2]
df_etf['% of Program Allocation'] = df_etf.iloc[:,3] / smccf_pmccf_allocation

df_etf_funds = df_etf['Fund Name'].groupby(df_etf.iloc[:,1]).nunique().count()
df_etf_value = sum(df_etf.iloc[:,3])
df_etf_value_str = '${:,.2f}'.format(df_etf_value)
df_etf_allocation = '{:.2%}'.format(sum(df_etf.iloc[:,4]))

print("SMCCF: Roughly " + df_etf_value_str + " Invested in " + str(df_etf_funds) + " Unique ETFs")
print("SMCCF: " + str(df_etf_allocation) + " of PMCCF/SMCCF Allocation Invested in Bond ETFs")


# # Eventually would like to use ETF tickers to search ETF holdings and append implied bond holdings to df_bond.
# etf_tickers = []
# for ticker in df_etf['Ticker']:
#     etf_tickers.append(ticker)
# etf_tickers = etf_tickers[:-2]


# MLF raw data sheet has 1 tab. Care about: number of issuers (governments) represented, face value when entered into transaction, and % of total allocation. See commented out code above (starting line 48) for requests/bs4 pull when we decide to make the excel pull dynamic.
mlf_excel = 'MLF-6-15-2020.xlsx'

df_mlf = pd.read_excel(open(mlf_excel,'rb'), sheet_name='MLF')
df_mlf['% of Program Allocation'] = df_mlf.iloc[:,6] / mlf_allocation

df_mlf_govts = df_mlf['Issuer name'].groupby(df_mlf.iloc[:,1]).nunique().count()
df_mlf_value = sum(df_mlf.iloc[:,6])
df_mlf_value_str = '${:,.2f}'.format(df_mlf_value)
df_mlf_allocation = '{:.2%}'.format(sum(df_mlf.iloc[:,12]))

print("MLF: " + df_mlf_value_str + " Invested in " + str(df_mlf_govts) + " Governments")
print("MLF: " + str(df_mlf_allocation) + " of MLF Allocation Invested")


# PPLF raw data sheet has 2 tabs, but only focusing on the 1st. Care about: number of institutions backed, number of loans issued, total amount issued, and % of total allocation. See commented out code above (starting line 48) for requests/bs4 pull when we decide to make the excel pull dynamic.
ppplf_excel = 'PPPLF-6-10-20.xlsx'

df_ppplf = pd.read_excel(open(ppplf_excel,'rb'), sheet_name='Detailed Report')
df_ppplf.drop(df_ppplf.columns[[0,1,2,4,5,6,7,9,10,11]], axis=1, inplace=True)
df_ppplf['% of Program Allocation'] = df_ppplf.iloc[:,1] / ppp_allocation

df_ppplf_lenders = df_ppplf['Institution Name'].groupby(df_ppplf.iloc[:,0]).nunique().count()
df_ppplf_loans = df_ppplf['Institution Name'].count()
df_ppplf_amount = sum(df_ppplf.iloc[:,1])
df_ppplf_amount_str = '${:,.2f}'.format(df_ppplf_amount)
df_ppplf_allocation = '{:.2%}'.format(sum(df_ppplf.iloc[:,2]))

print("PPPLF: " + str(df_ppplf_lenders) + " PPP Lenders Backed Via " + df_ppplf_amount_str + " Across " + str(df_ppplf_loans) + " Loans")
print("PPPLF: " + str(df_ppplf_allocation) + " of PPP Allocation ($669B) Backed")

print("TOTAL: " + ('${:,.2f}'.format(df_bond_cost+df_etf_value+df_mlf_value+df_ppplf_loans)) + " in Total COVID-Related Fed Balance Sheet Expansion")