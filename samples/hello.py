from nagi import db
from nagi.leaderboard import leaderboard
from nagi.thing import thing_setup, Thing
from nagi.model import  Entry

# setup db setting 
# pool_opt sets the db pool min connections and max connections
db.setup('localhost', 'test', 'test', 'nagi', pool_opt={'minconn': 3, 'maxconn': 10})

# setup thing_setup, initilaize the thing_setup bind the data-mapper
thing_setup() 

use the leaderboard api
lb = leaderboard(leaderboard_id=2) # find leaderboard by leaderboard_id
lb = leaderboard(name='name')  # load leaderboard by name
lb.rank_for_user(12) # rank a user by user id
lb.rank_for_users([12, 2]) # rank users by users

###################
  DB AND Model   #
###################

# Entry and DB backed
entry = Entry(23, 2, 23)
Thing('entry').save(entry)
entry = Thing('entry').find(2, 23)
print entry

