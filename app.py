#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#
import re
from models import Artist, show, db_setup, Venue
from datetime import datetime
import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
import sys
from flask_migrate import Migrate
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = db_setup(app)

# TODO: connect to a local postgresql database
migration = Migrate(app, db)
#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))

    # TODO: implement any missing fields, as a database migration using Flask-Migrate
    website = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean)
    seeking_description = db.Column(db.Text)
    upcoming_shows_count = db.Column(db.Integer)
    past_shows_count = db.Column(db.Integer)
    shows = db.relationship('Show', backref='venue', lazy=True, cascade='save-update, delete, merge')


class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))

    # TODO: implement any missing fields, as a database migration using Flask-Migrate
    website = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean)
    seeking_description = db.Column(db.Text)
    upcoming_shows_count = db.Column(db.Integer)
    past_shows_count = db.Column(db.Integer)
    shows = db.relationship('Show', backref='artist', lazy=True, cascade='save-update, delete, merge')

# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.
class Show(db.model):
  __tablename__ = 'shows'
  id = db.Column(db.Integer, primary_key = True)
  begin_time = db.Column(db.Datetime)
  venue_id = db.Column(db.Integer, db.ForegnKey('Venue.id'))
  artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'))
  upcoming = db.Column(db.Boolean)
#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
  location = db.session.query(Venue.city, Venue.state).group_by(Venue.city, Venue.state).all()
  data = []
  for loca in location:
    venues = db.session.query(Venue.id, Venue.name, Venue.upcoming_shows).filter(Venue.city==loca[0], Venue.state==loca[1]).all()
    data.append({
      'city': loca[0],
      'state': loca[1],
      'venues': []
    })
    for venue in venues:
      data[-1]['venues'].append({
        'id': venue[0],
        'name': venue[1],
        'num_upcoming_shows': venue[2]
      })
  return render_template('pages/venues.html', areas=data);
  


@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on venues with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  result = Venue.query.filter(Venue.name.ilike('% {} %'.format(request.form['search_term']))).all()
  response={
    "count": len(result),
    "data": []
  }
  for venue in result:
    response['data'].append({
    "id": venue.id,
      "name": venue.name,
      "num_upcoming_shows": venue.upcoming_shows,
    })
      
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  venue = Venue.query.get(venue_id)
  past_shows = []
  upcoming_shows = []
  shows = venue.shows
  data = []
  for show in shows:
    show_data = {
      'artist_id': show.artist.id,
      'artist_name' : show.artist.name,
      'artist_image_link': show.artist.image_link,
      'begin_time': str(show.begin_time),
    }
    if(show.upcoming):
      upcoming_shows.append(show_data)
    else:
      past_shows.append(show_data)
  data1={
    "id": venue.id,
    "name": venue.name,
    "genres": venue.genres.split(','),
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link,
    "past_shows": venue.past_shows,
    "upcoming_shows": venue.upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows)
  }

  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  new_venue = Venue()
  new_venue.name = request.form['name']
  new_venue.city = request.form['city']
  new_venue.state = request.form['state']
  new_venue.phone = request.form['phone']
  new_venue.address = request.form['address']
  new_venue.facebook_link = request.form['facebook_link']
  new_venue.image_link = request.form['image_link']
  new_venue.website = request.form['website']
  new_venue.genres = request.form['genres']

  # on successful db insert, flash success
  try:
    db.session.add(new_venue)
    db.session.commit()
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  except:
    db.session.rollback()
  # TODO: on unsuccessful db insert, flash an error instead.
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
  # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  finally:
    db.session.close()
  return redirect(url_for('index'))

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  venue_id = request.form.get('venue_id')
  venue_deleted = Venue.query.get(venue_id)
  NameOfVenue = venue_deleted.name

  try:
    db.session.delete(venue_deleted)
    db.session.commit()
    flash('Venue ' + NameOfVenue + ' was successfully listed!')
  except:
    db.session.rollback()
    flash('An error occurred. Venue ' + NameOfVenue + ' could not be listed.')

  finally:
    db.session.close()
  return redirect(url_for('index'))

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  data= Artist.query.with_entities(Artist.id, Artist.name).all()
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  result = Artist.query.filter(Artist.name.ilike('% {} %'.format(request.form['search_term']))).all()
  response= {
    'count': len(result),
    'data': []
  }
  for artist in result:
    response['data'].append({
      'id': artist.id,
      'name': artist.name,
      'num_upcoming_shows': artist.upcomimg_shows_count
    })
  return render_template('pages/search_artists.html', result=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # TODO: replace with real artist data from the artist table, using artist_id
  artist = Artist.query.get(artist_id)
  shows = artist.shows
  upcoming_shows = []
  past_shows = []
  data = []
  for show in shows:
      show_data = {
        'venue_id': show.venue.id,
        'venue_name' : show.venue.name,
        'venue_image_link': show.venue.image_link,
        'begin_time': str(show.begin_time),
    }
      if(show.upcoming):
        upcoming_shows.append(show_data)
      else:
        past_shows.append(show_data)
  data ={
    "id": artist.id,
    "name": artist.name,
    "genres": artist.genres.split(','),
    "address": artist.address,
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website": artist.website,
    "facebook_link": artist.facebook_link,
    "seeking_talent": artist.seeking_talent,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link,
    "past_shows": artist.past_shows,
    "upcoming_shows": artist.upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows)
  }
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist_id = request.args.get('artist_id')
  artist = Artist.query.get(artist_id)
  artist_data={
    "id": artist.id,
    "name": artist.name,
    "genres": artist.genre,
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website": artist.website,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link
  }
  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  artist = Venue()
  artist.name = request.form['name']
  artist.city = request.form['city']
  artist.state = request.form['state']
  artist.phone = request.form['phone']
  artist.address = request.form['address']
  artist.facebook_link = request.form['facebook_link']
  artist.image_link = request.form['image_link']
  artist.website = request.form['website']
  artist.genres = request.form['genres']

  try:
    db.session.commit()
    flash('Artist {} is successfully updated!'.format(artist.name))
  except:
    db.session.rollback()
    flash('Artist is not updated.')

  finally:
    db.session.close()
  return redirect(url_for('index'))


  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue_id = request.args.get('venue_id')
  venue = Venue.query.get(venue_id)
  venue_data = {
    "id": venue.id,
    "name": venue.name,
    "genres": venue.genres.split(','),
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link
    
  }
  
  
  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue_data)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributesrtist = Venue()
  venue = Venue.query.get(venue_id)
  venue.name = request.form['name']
  venue.city = request.form['city']
  venue.state = request.form['state']
  venue.phone = request.form['phone']
  venue.address = request.form['address']
  venue.facebook_link = request.form['facebook_link']
  venue.image_link = request.form['image_link']
  venue.website = request.form['website']
  venue.genres = request.form['genres']
  try:
    db.session.commit()
    flash('Venue ' + request.form['name'] + ' was successfully updated!')
  except:
    db.session.rollback()
    flash('An error occurred. Venue ' + venue.name + ' could not be updated.')

  finally:
    db.session.close()
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  new_artist = Artist
  new_artist.name = request.form['name']
  new_artist.city = request.form['city']
  new_artist.state = request.form['state']
  new_artist.phone = request.form['phone']
  new_artist.facebook_link = request.form['facebook_link']
  new_artist.image_link = request.form['image_link']
  new_artist.website = request.form['website']
  new_artist.genres = request.form['genres']

  # on successful db insert, flash success
  try:
    db.session.add(new_artist)
    db.session.commit()
    flash('Artist' + request.form['name'] + ' was successfully listed!')
  except:
    db.session.rollback()
  # TODO: on unsuccessful db insert, flash an error instead.
    flash('An error occurred. Venue ' + new_artist.name + ' could not be listed.')
  # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  finally:
    db.session.close()
  return redirect(url_for('index'))



#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  shows_list = Show.query.all()
  data = []
  for show in shows_list:
    if(show.upcoming):
      data.append({
        'venue_id': show.venue_id,
        'venue_name': show.venue.name,
        'artist_id': show.artist_id,
        'artist_name': show.artist.name,
        'artist_image_link': show.artist.image_link,
        'begin_time': str(show.begin_time)

      })
  
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead
  new
  # on successful db insert, flash success
  flash('Show was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Show could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
