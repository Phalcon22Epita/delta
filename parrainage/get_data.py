import requests

def fetch_data():
    url = "https://static.data.gouv.fr/resources/parrainages-des-candidats-a-lelection-presidentielle-francaise-de-2022/20220307-183308/parrainagestotal.csv"
    req = requests.get(url, allow_redirects=True)
    csv_file = open('parrainage/data/parrainagestotal.csv', 'wb')
    csv_file.write(req.content)
    csv_file.close()