heroku ps:scale web=1
web: gunicorn test:app
curl -X POST -H "Content-Type: application/json" -d '{
  "setting_type":"greeting",
  "greeting":{
    "text":"Timeless apparel for the masses."
  }
}' "https://graph.facebook.com/v2.6/me/thread_settings?access_token=EAAIeJYNmvk0BAPoIK8emOsfh5AYANJgcIklO3iw64gbBuHVM0yQslminOZBNCzfVryDeGHa4wXGmqTckUpuMmAzcmvxmYNc08finvPMzvzEOOpN52jsRtmGp0j8J1S6n4xW7x5RLmEZCRa7ZCkLqHeNgQ6f8aea10xpInW0KAZDZD"