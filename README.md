# mt-payback

A silly small webapp that tries to make it as easy as possible to submit payback requests when Mälartåg trains are delayed or cancelled.

When slowly exiting my WFH bubble after the main phase of the 2020+ pandemic, I got fed up with how often trains were now cancelled or delayed, but I never had the energy to actually fill in the form to get my money back. In the time I spent on making this I could probably have submitted 50+ requests manually, but hey that wouldn't have been as fun, right?

# Installing and running

* Run `pip install -r requirements.txt`
* Run the app.py file
* Visit http://localhost:5000

When you enter a new ticket, it will be stored and used as the default choice for subsequent page loads until the current date is past the ticket's expiry date.

# Limitations

The list of departure and arrival stations is hardcoded in the app. It would be easy enough to include them all, but then it would take a longer time to choose departure and arrival stations. You could change to others as you see fit. The full list of stations along with their names and codes are available here: https://evf-regionsormland.preciocloudapp.net/api/TrainStations