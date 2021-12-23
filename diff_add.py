import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials


name = f'https://docs.google.com/spreadsheets/d/1EE64POwwmAmjIZ3BuaqfHFeOEWrCwGouTxCN-9ounhA/gviz/tq?tqx=out:csv&sheet=FullTime'
results_df = pd.read_csv(name)


def alphas(row):
    if row['Odds'] == '-':
        return ('')
    else:
        try:
            stoix = float(row['Odds'].replace(',', '.'))
            mine = float(row['Prediction %'].replace(',', '.'))
        except:
            stoix = float(row['Odds'])
            mine = float(row['Prediction %'])

    try:
        tempvar = round((stoix - (1/mine))*100,2)
    except:
        tempvar = '-'

    return (tempvar)

results_df['diff %'] = results_df.apply(lambda row: alphas(row), axis=1)


results_df['Date'] = pd.to_datetime(results_df['Date'], format='%d/%m/%Y')
results_df.sort_values(by=['Date', 'Time', 'HomeTeam'], inplace=True, ascending=True)
results_df['Date'] = results_df['Date'].dt.strftime('%d/%m/%Y')
results_df.fillna('', inplace=True)



json_creds = {
  "type": "service_account",
  "project_id": "share-betting",
  "private_key_id": "f978bc9098c12a4d8831bb7102981d37f589a832",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQDF0WUc65p8EIeP\nIaNYUmgBWLWoe9gMxyBAhm9wPbFEqL25UvP2PCsihyE0fOnUuwB9chgxVc0imWde\nppyoVmHJ/htGZN8Lk5iTv86Bluqc9d9dNz/fzXRPsYnlr9Sp4WGLBStJKtX70p3G\nDU2fC+c3uIN5+5WDi/7fThnPdBzj/0zkRK+pphdCRly5RPT+/nP1gelOMoKLPwMd\nz2uRpllsc0fbb1VgJ+58mLjOGfk6q23tgdXiSvYAj1LsicapM4A6LMrqrSps3tti\nmDBaS+SGrzSO4OQQyoqeDTErIt+RyCjecatq7vP+AuRYCyEuAjGsidCz9QRZ8yho\n54KIpUQjAgMBAAECggEADpgTMJ4FKLADgEDID0UNHURRKpvwZYjvTTNd11cF0/3q\n+VgwXXM073gur/OjQKmHMLoRJNqiprHQmYALQLQWxNM1ae0ZM35xHD1jW9Ypeuj8\n0KC52qYKtbJwbPya4Omay6nW9q/tV4XDVBA5MMmtBkRbls1Dy4+xfwIBD3gOhZd3\nyYQNHWg8XcI4Eez7LIr9UbSnbQw9xYylHwFW0mRq/uuUL/QBmd0ux1eHFc0fl3+9\noEzNquGQL/1Wvth9Gp6ShIVuj7IJM2p3vezyn1ehkgBoKpkd8JkFn15Mt0kQ4ZJO\naqfUvrnRQllSeH04ls801S9jFErWnXwDKfBMmbIzAQKBgQD7TU1rMBPh11ApuPAF\noK/9cexkh09vBTdJM6FmLWukiYSnXcTWZRXwVZ6Km5tn3rdMpslUhqlcdDsem9Co\nMnzkGatjbzTVAN49j8d+bLDGWAvBSRA82Fib8plEZlp+YtWrvOIxzdXE7qDS4Fjk\nt1Mh//iaMGL4vPIVGBBk2roQgQKBgQDJhCAOccTxstVGbN72mCtQMkIsNkCyUs7g\n2XodjLilx1DxvJwrwShNcIE57yJrNEdNsmSIXRn/jFqgABJxlc984hVVoeDN2lyu\n9SQ3f6yKy+SelVOrUAIzsTprcMRYyLI2IX6QTG4PH8QVSi2L1HbZpawmK5OV8oij\nmYMqfivCowKBgQDv8q+pWQ6i5WO1ctA7j2J7LPv6QPinmONhEdtaJKRTRrtS00XP\nMFXyVM48qreIRi/fEKHMA4hSruiEIWLqNsrpQVlUaCqZ92o8fbyOCloACLGwrILE\nlg6FWO7fUJu3ccdzY7bWtyMWFoOY1n4KZMEMBczp7KmTt1Wurnt40SA4AQKBgGU0\nmCzo8nI40GgIMYpDLi2esCEoNiHY+NFwJ6ZDkFCh44MkqIJJBgauZBhGg1C39r+M\nwnTB3Va8lJ8aqiilhok/ultBa3e3HSk5MLE2y98BO5ZxhI3bJt/zOFXRUqsMUIRj\nGf86g2PRHlda47kAQZhZXjXlWL/MCNexN3DV4QBlAoGAaraexVDmEmAlC8X9RBM3\nOWNdgJAlBWeI10YfaLrRPkYAtO9gqUGBdt+/Hi0bqisWhS8ZbTtTOw698Sbp5DVV\nCAclQHRjVqMcDD/4x5zpSsPaOB+LYvLYqcR5sEjgCPv983W2fn7fIoVDEaK0zE27\n5RDP3PJyQr2ybaSRkY02wD0=\n-----END PRIVATE KEY-----\n",
  "client_email": "spyfaq-laptop@share-betting.iam.gserviceaccount.com",
  "client_id": "114439080508189477603",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/spyfaq-laptop%40share-betting.iam.gserviceaccount.com"
}
credentials = ServiceAccountCredentials.from_json_keyfile_dict(json_creds)
file = gspread.authorize(credentials)
sheet = file.open("Betting")
sheet = sheet.worksheet('FullTime')

sheet.update('A2', results_df.values.tolist())