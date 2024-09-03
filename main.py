import scrapy
import pandas as pd

class PokemonScrapper(scrapy.Spider):
    name = 'pokemon_scrapper'
    domain = "https://pokemondb.net/"
    start_urls = ["https://pokemondb.net/pokedex/all"]

    def __init__(self, *args, **kwargs):
        super(PokemonScrapper, self).__init__(*args, **kwargs)
        self.data = []

    def parse(self, response):
        pokemons = response.css('#pokedex > tbody > tr')
        for pokemon in pokemons:
            link = pokemon.css("td.cell-name > a::attr(href)").extract_first()
            yield response.follow(self.domain + link, self.parse_pokemon)

    def parse_pokemon(self, response):
        pokemon_number = response.css('.vitals-table > tbody > tr:nth-child(1) > td > strong::text').get()
        pokemon_name = response.css('#main > h1::text').get()
        next_evolution = response.css('#main > div.infocard-list-evo > div:nth-child(3) > span.infocard-lg-data.text-muted > a::text').get()
        next_evolution_url = response.css('#main > div.infocard-list-evo > div:nth-child(3) > span.infocard-lg-data.text-muted > a::attr(href)').get()
        next_evolution_number = response.css('#main > div.infocard-list-evo > div:nth-child(3) > span.infocard-lg-data.text-muted > small::text').get()
        weight = response.css('.vitals-table > tbody > tr:contains("Weight") > td::text').re_first(r'(\d+\.\d+)')
        height = response.css('.vitals-table > tbody > tr:contains("Height") > td::text').re_first(r'(\d+\.\d+)')
        types = response.css('.vitals-table > tbody > tr:contains("Type") > td a::text').getall()

        abilities = response.css('.vitals-table tr:contains("Abilities") td a::text').getall()
        abilities_urls = response.css('.vitals-table tr:contains("Abilities") td a::attr(href)').getall()
        abilities_urls = [response.urljoin(url) for url in abilities_urls]

        for ability, ability_url in zip(abilities, abilities_urls):
            yield response.follow(ability_url, self.parse_habilidades, meta={
                'pokemon_number': pokemon_number,
                'pokemon_url': response.url,
                'pokemon_name': pokemon_name,
                'next_evolution': next_evolution,
                'next_evolution_url': response.urljoin(next_evolution_url) if next_evolution_url else None,
                'next_evolution_number': next_evolution_number,
                'height': height,
                'weight': weight,
                'types': types,
                'ability_name': ability,
                'ability_url': ability_url
            })

    def parse_habilidades(self, response):
        ability_name = response.meta['ability_name']
        pokemon_number = response.meta['pokemon_number']
        pokemon_url = response.meta['pokemon_url']
        pokemon_name = response.meta['pokemon_name']
        next_evolution = response.meta['next_evolution']
        next_evolution_url = response.meta['next_evolution_url']
        next_evolution_number = response.meta['next_evolution_number']
        height = response.meta['height']
        weight = response.meta['weight']
        types = response.meta['types']
        ability_url = response.meta['ability_url']

        # Extraindo a descrição da habilidade.
        description = response.css('.grid-row > .grid-col > p::text').get()

        # Salvar os dados em uma lista
        self.data.append({
            'number': pokemon_number,
            'pokemon_url': pokemon_url,
            'name': pokemon_name,
            'next_evolution_number': next_evolution_number,
            'next_evolution_name': next_evolution,
            'next_evolution_url': next_evolution_url,
            'height': height,
            'weight': weight,
            'types': ', '.join(types),
            'ability_name': ability_name,
            'ability_url': ability_url,
            'ability_description': description
        })

    def closed(self, reason):
        # Ao final da execução, converte os dados coletados em um DataFrame do pandas
        df = pd.DataFrame(self.data)

        # Salva o DataFrame em um arquivo CSV
        df.to_csv('pokemon_data.csv', index=False)
