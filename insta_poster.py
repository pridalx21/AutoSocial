import requests

class InstagramPoster:
    def __init__(self, access_token):
        self.access_token = access_token
        self.api_url = 'https://graph.instagram.com/'

    def post_image(self, image_path, caption):
        # Schritt 1: Bild hochladen
        upload_url = f'{self.api_url}me/media'
        image_data = {'image_url': image_path, 'caption': caption}
        response = requests.post(upload_url, data=image_data, params={'access_token': self.access_token})

        if response.status_code == 200:
            media_id = response.json()['id']
            # Schritt 2: Bild veröffentlichen
            publish_url = f'{self.api_url}me/media_publish'
            publish_response = requests.post(publish_url, data={'creation_id': media_id}, params={'access_token': self.access_token})
            return publish_response.json()
        else:
            return response.json()

# Beispielverwendung:
# poster = InstagramPoster('DEIN_ACCESS_TOKEN_HIER')
# result = poster.post_image('URL_ZUM_BILD', 'Dein Werbetext hier')
# print(result)
