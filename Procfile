heroku ps:scale web=1
curl -X POST -H "Content-Type: application/json" -d '{
  "setting_type":"call_to_actions",
  "thread_state":"new_thread",
  "call_to_actions":[
    {
      "payload":"new_bet"
    }
  ]
}' "https://graph.facebook.com/v2.6/me/thread_settings?access_token=EAAIeJYNmvk0BACXjV9sUcwwNnfg0EM2y5zv2prZAH6ilxX9ouAHZBM1ZC9Hn96cUSVRCtK5fXuo1qnbZAMZC0jysfdhURw5Kq6VmB0g80AX9LpZCF7Ro0NcOXZCR4ZBCfvAsGU4aeRJD8mZBaGhBzZB00x5bbOZAluuS7IelpZAOTPbq1AZDZD"
web: gunicorn backup:app
