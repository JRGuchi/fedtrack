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
pd.set_option('display.width', 500)

# Main website we will be pulling information from.
fed_url = 'https://www.federalreserve.gov/publications/reports-to-congress-in-response-to-covid-19.htm'

# Lending facilities we'll be tracking. Note that hrefs are partial for date flexibility.
pdcf_title = 'Primary Dealer Credit Facility' # No transaction-specific disclosures as of yet.
pdcf_allocation = 0

cpff_title = 'Commercial Paper Funding Facility' # No transaction-specific disclosures as of yet.
cpff_allocation = 0

mmmflf_title = 'Money Market Mutual Fund Liquidity Facility' # No transaction-specific disclosures as of yet.
mmmflf = 0

talf_title = 'Term Asset-Backed Securities Loan Facility' # First updated July 10, 2020.
talf_allocation = 100000000000

smccf_title = 'Secondary Market Corporate Credit Facility' # Includes PMCCF and SMCCF. First updated May 29, 2020.
smccf_href = '/publications/files/smccf-transition-specific-disclosures-'
pmccf_title = 'Primary Market Corporate Credit Facility'
smccf_pmccf_allocation = 750000000000

mlf_title = 'Municipal Liquidity Facility' # First updated June 15, 2020.
mlf_href = '/publications/files/MLF-transaction-specific-disclosures-'
mlf_allocation = 500000000000

ppplf_title = 'Paycheck Protection Program Liquidity Facility' # First updated May 15, 2020.
ppplf_href = '/publications/files/PPPLF-transaction-specific-disclosures-'
ppp_allocation = 669000000000

mself_title = 'Main Street Expanded Loan Facility' # No transaction-specific disclosures as of yet. Not operational yet.
mself_allocation = 0


msnlf_title = 'Main Street New Loan Facility' # No transaction-specific disclosures as of yet. Not operational yet.
msnlf_allocation = 0


msplf_title = 'Main Street Priority Loan Facility' # No transaction-specific disclosures as of yet. Not operational yet.
msplf_allocation = 0
    

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

# TALF, SMCCF, MLF, and PPPLF are frequently updated with transaction-specific disclosures. I am putting manual data first, and then focusing on the programs with transaction-specific updates.
df_pdcf_cost = 2489100000
df_pdcf_cost_str = '${:,.2f}'.format(df_pdcf_cost)
print("PDCF: " + df_pdcf_cost_str + " Currently Outstanding")

df_cpff_cost = 4242570889
df_cpff_cost_str = '${:,.2f}'.format(df_cpff_cost)
print("CPFF: " + df_cpff_cost_str + " Currently Outstanding")

df_mmmflf_cost = 21442189003
df_mmmflf_cost_str = '${:,.2f}'.format(df_mmmflf_cost)
print("MMMFLF: " + df_mmmflf_cost_str + " Currently Outstanding")


# TALF
# def talf_data():
#     resp = requests.get(fed_url)
#     soup = bs.BeautifulSoup(resp.text, "lxml")


# TALF raw data sheet has 3 tabs. We care about: the initial loan amount and initial collateral market value, what that implied discount is, the number of borrowers, and the number of issuers. Maybe we'll care about material investors later (2nd tab). See commented out code above for requests/bs4 pull when we decide to make the excel pull dynamic.
talf_excel = 'TALF-7-10-20.xlsx'


df_talf = pd.read_excel(open(talf_excel, 'rb'), sheet_name='TALF Loan Level Data')
df_talf.drop(df_talf.columns[[0, 1, 2, 4, 5, 12, 14, 16]], axis=1, inplace=True)
df_talf['Discount to Collateral'] = df_talf.iloc[:,1] / df_talf.iloc[:,7]
df_talf['% of Program Allocation'] = df_talf.iloc[:,1] / talf_allocation

df_talf_issuers = df_talf['Issuer'].nunique()
df_talf_cost = sum(df_talf.iloc[:,1])
df_talf_cost_str = '${:,.2f}'.format(df_talf_cost)
df_talf_collateral = sum(df_talf.iloc[:,7])
df_talf_allocation = '{:.2%}'.format(sum(df_talf.iloc[:,11]))

print("TALF: " + df_talf_cost_str + " Invested in " + str(df_talf_issuers) + " Issuers")
print("TALF: " + str(df_talf_allocation) + " of TALF Allocation ($100B) Invested")


# SMCCF raw data sheet has 6 tabs. We care about 4 tabs: the current bond position summary, sector breakdown, credit breakdown, and current ETF position summary. See commented out code above for requests/bs4 pull when we decide to make the excel pull dynamic.
smccf_excel = 'SMCCF-7-10-20.xlsx'

# Cleaned current bond position summary (using amortized cost, not par value). Care about: number of issuers represented in the dataset, total amortized cost, and % of total allocation.
df_smccf = pd.read_excel(open(smccf_excel,'rb'), sheet_name='Position Summary-Bond')
df_smccf.drop(df_smccf.columns[[2, 3, 5]], axis=1, inplace=True)
df_smccf = df_smccf[:-2]
df_smccf['% of Program Allocation'] = df_smccf.iloc[:,3] / smccf_pmccf_allocation

df_smccf_issuers = df_smccf['Issuer'].groupby(df_smccf.iloc[:,0]).nunique().count()
df_smccf_cost = sum(df_smccf.iloc[:,3])
df_smccf_cost_str = '${:,.2f}'.format(df_smccf_cost)
df_smccf_allocation = '{:.2%}'.format(sum(df_smccf.iloc[:,4]))

print("SMCCF: " + df_smccf_cost_str + " Invested in " + str(df_smccf_issuers) + " Issuers")
print("SMCCF: " + str(df_smccf_allocation) + " of PMCCF/SMCCF Allocation ($750B) Invested in Individual Bonds")


# Cleaned current bond position sector exposure as a % of total cost. Care about: sector composition.
df_smccf_sectors = pd.read_excel(open(smccf_excel,'rb'), sheet_name='Sector Summary-Bond')
df_smccf_sectors = df_smccf_sectors[:-2]

sector_data = df_smccf_sectors.iloc[:,1]
sector_labels = df_smccf_sectors.iloc[:,0]

fig1, ax1 = plt.subplots()
ax1.pie(sector_data, labels=sector_labels, autopct='%.1f%%', labeldistance=1.1, pctdistance=0.9, startangle=90)
ax1.axis('equal')
plt.title("SMCCF Sector Composition", pad=25)

# plt.show()


# Cleaned current SMCCF bond position credit exposure.
df_smccf_credit = pd.read_excel(open(smccf_excel,'rb'), sheet_name='Rating&WAM-Bond')
df_smccf_credit.drop(df_smccf_credit.columns[3:], axis=1, inplace=True)
df_smccf_credit.drop(df_smccf_credit.index[0], inplace=True)
df_smccf_credit = df_smccf_credit[:-5] # Includes removing WAM

credit_data = df_smccf_credit.iloc[:,1]
credit_labels = df_smccf_credit.iloc[:,0]

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
mlf_excel = 'MLF-7-10-20.xlsx'

df_mlf = pd.read_excel(open(mlf_excel,'rb'), sheet_name='MLF-Detailed_report')
df_mlf['% of Program Allocation'] = df_mlf.iloc[:,6] / mlf_allocation

df_mlf_govts = df_mlf['Issuer Name'].groupby(df_mlf.iloc[:,1]).nunique().count()
df_mlf_value = sum(df_mlf.iloc[:,6])
df_mlf_value_str = '${:,.2f}'.format(df_mlf_value)
df_mlf_allocation = '{:.2%}'.format(sum(df_mlf.iloc[:,12]))

print("MLF: " + df_mlf_value_str + " Invested in " + str(df_mlf_govts) + " Governments")
print("MLF: " + str(df_mlf_allocation) + " of MLF Allocation ($500B) Invested")


# PPLF raw data sheet has 2 tabs, but only focusing on the 1st. Care about: number of institutions backed, number of loans issued, total amount issued, and % of total allocation. See commented out code above (starting line 48) for requests/bs4 pull when we decide to make the excel pull dynamic.
ppplf_excel = 'PPPLF-7-10-20.xlsx'

df_ppplf = pd.read_excel(open(ppplf_excel,'rb'), sheet_name='Detailed_Report')
df_ppplf.drop(df_ppplf.columns[[0,1,2,4,5,6,7,9,10,11]], axis=1, inplace=True)
df_ppplf['% of Program Allocation'] = df_ppplf.iloc[:,1] / ppp_allocation

df_ppplf_lenders = df_ppplf['Institution Name'].groupby(df_ppplf.iloc[:,0]).nunique().count()
df_ppplf_loans = df_ppplf['Institution Name'].count()
df_ppplf_amount = sum(df_ppplf.iloc[:,1])
df_ppplf_amount_str = '${:,.2f}'.format(df_ppplf_amount)
df_ppplf_allocation = '{:.2%}'.format(sum(df_ppplf.iloc[:,2]))

print("PPPLF: " + str(df_ppplf_lenders) + " PPP Lenders Backed Via " + df_ppplf_amount_str + " Across " + str(df_ppplf_loans) + " Loans")
print("PPPLF: " + str(df_ppplf_allocation) + " of PPP Allocation ($669B) Backed")

print("TOTAL: " + ('${:,.2f}'.format(df_pdcf_cost+df_cpff_cost+df_mmmflf_cost+df_talf_cost+df_smccf_cost+df_etf_value+df_mlf_value+df_ppplf_loans)) + " in Total COVID-Related Fed Balance Sheet Expansion")


# Testing comment2