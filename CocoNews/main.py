import requests
import time as t
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin

class Site :
    def __init__(self,site_url,teasers,titles,urls,name) :
        self.section = teasers
        self.site_url = site_url
        self.titles = titles
        self.urls = urls
        self.name = name
        
class Article :
    def __init__(self,site,title,url,date,hour) :
        self.title = title
        self.url = url
        self.site = site
        self.state = 'unwritten'
        self.article = self.get_true_link()
        self.date = date
        self.hour = hour
        
    def get_true_link(self) -> str :
        return urljoin(self.site.site_url, self.url)
    
    def is_unwritten(self) -> bool :
        return self.state == 'unwritten'
        
    def __repr__(self) :
        return f'Article de {self.site.name}'
    
    
URLS = [
        Site('https://www.lemonde.fr/actualite-en-continu/','teaser','teaser__title','teaser__link','Le Monde'),
        Site('https://www.streetpress.com/','articlePreview','title','a','Street Press'),
        Site('https://www.mediapart.fr/journal/fil-dactualites','block','h2','teaser-link','Mediapart'),
        Site('https://www.blast-info.fr/articles','col-span-12','h3','a','Blast'),
        Site('https://www.franceinfo.fr/grands-formats/','card-article-l','card-article-l__title','a','France Info'),
        Site('https://www.humanite.fr/en-continu','ongoing-component__elements__line','h2','a','L\'Humanité'),
        Site('https://www.liberation.fr/fil-info/','custom-card-list','h2','a','Libération'),
        Site('https://disclose.ngo/fr/impact','entry','h2','a','Disclose'),
        Site('https://www.monde-diplomatique.fr/','unarticle','h3','parenta','Le Monde Diplomatique'),
        Site('https://orientxxi.info/tout','lire_dossier','titre','a','Orient XXI'),
        Site('https://afriquexxi.info/tout','lire_dossier','titre','a','Afrique XXI')
        ]

def scrap(site:Site,articlesDB,doc) :
    url = site.site_url
    page = requests.get(url)
    soup = BeautifulSoup(page.content,'html.parser')
    articles = []
    existing_titles = [h1.get_text() for h1 in doc.find_all('h1')]
    for teaser in soup.find_all(class_=site.section) :
        if site.titles in ('h2','h3','a') :
            title_tag = teaser.find(site.titles) 
        else :
            title_tag = teaser.find(class_=site.titles)
        if title_tag and title_tag.get_text() not in existing_titles:
            if site.urls == 'a' :
                url_tag = teaser.find('a')
            elif site.urls == 'parenta' :
                url_tag = teaser.parent
                if url_tag :
                    url_tag = url_tag.find('a')
            else : 
                url_tag = teaser.find(class_=site.urls)
            if title_tag and url_tag :
                url = url_tag.get('href')
                title = title_tag.get_text()
                article = Article(site,title,url,datetime.now().strftime("%d/%m/%Y").replace('/','-'),datetime.now().strftime("%H:%M"))
                if not article in articles : 
                    articles.append(article)
    return articles
    
def scrap_all(sites:list[Site],articlesDB,doc):
    articles = []
    for site in sites :
        articles.extend(scrap(site,articlesDB,doc))
    return articles
    
def write_html(article:Article,doc) :
    content = doc.find(class_='content')
    if content and article.is_unwritten() :
        new_article = doc.new_tag('article')
        
        new_div = doc.new_tag('div')
        new_div['class'] = 'meta-bar'
        
        new_a = doc.new_tag('a')
        new_a['href'] = article.article
        new_a['target'] = '_blank'
        
        new_date = doc.new_tag('time')
        new_date['datetime'] = article.date + 'T' + article.hour
        new_date.append(f"{article.date.replace('-','/')} à {article.hour}")
        
        new_h1 = doc.new_tag('h1')
        new_h1.string = article.title
        
        new_src = doc.new_tag('a')
        new_src['class'] = 'src'
        new_src['href'] = article.site.site_url
        new_src['target'] = '_blank'
        new_src.string = f'{article.site.name}'
        
        new_a.append(new_h1)
        new_div.append(new_src)
        new_div.append(new_date)
        new_article.append(new_div)
        new_article.append(new_a)
        
        content.insert(0,new_article)
        article.state = 'written'
        
def purger_doublons_existants(doc):
    deja_vu = set()
    articles = doc.find_all('article')
    
    for art in reversed(articles):
        titre = art.find('h1').get_text(strip=True)
        if titre in deja_vu:
            art.decompose()
        else:
            deja_vu.add(titre)
        
if __name__ == '__main__':
    new_articles = []
    with open("index.html", "r", encoding="utf-8") as f:
        doc = BeautifulSoup(f, "html.parser")
    new_articles.extend(scrap_all(URLS,new_articles,doc))
    if len(new_articles) > 0 :
        existing_titles = set()
        for article in new_articles :
            if not article.title in existing_titles :
                write_html(article,doc)
                existing_titles.add(article.title)
        purger_doublons_existants(doc)
        all_articles = doc.find_all('article')
        if len(all_articles) > 1000:
            for old_art in all_articles[1000:]:
                old_art.decompose()
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(doc.prettify())
