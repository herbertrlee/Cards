import endpoints
import random
import json

from google.appengine.api import users
from google.appengine.api import urlfetch
from google.appengine.ext import ndb
from protorpc import remote
from protorpc import message_types
from protorpc import messages

from endpoints_proto_datastore.ndb import EndpointsModel
from endpoints_proto_datastore.ndb import EndpointsAliasProperty


GAME_STATUS_PENDING = 0
GAME_STATUS_WAITING_SUBMITS = 1
GAME_STATUS_WAITING_CZAR = 2
GAME_STATUS_COMPLETE = 3

SUBMISSION_STATUS_PENDING = 0 #Waiting for all the submissions to come in
SUBMISSION_STATUS_ACTIVE = 1 #All submissions are in, waiting for the czar to pick
SUBMISSION_STATUS_COMPLETE = 2 #Round is over

NO_ALERTS = 0
GAME_ALERT = 1
INVITATION_ALERT = 2
INACTIVE_ALERT = 3

API_KEY = "key=AIzaSyBZZxt2MJIgRh02i6AZsHVdcwPovjEZTF8"
GCM_URL = "https://android.googleapis.com/gcm/send"

WEB_CLIENT_ID = "502653129428-59d11p2m6avchdqgvrg6j6pm65ls2ph4.apps.googleusercontent.com"
ANDROID_CLIENT_ID = "583361565801-a6804nn0h0dcgjhqmuv0nbsfjijn7m2k.apps.googleusercontent.com"

#Local User information
class UserInfo(EndpointsModel):
  user = ndb.UserProperty()
  invitations = ndb.KeyProperty(repeated=True)
  regId = ndb.StringProperty()
  alias = ndb.StringProperty()
  
  @EndpointsAliasProperty(property_type=messages.BooleanField)
  def success(self):
    return True
  
#Player information.  Contains relevant information for a user in a particular game.
class Player(EndpointsModel):
  gameId = ndb.IntegerProperty()#Id of the game with which this player is associated
  user = ndb.UserProperty()#User who is this player in this game
  hand = ndb.IntegerProperty(repeated=True)#List of all the white card ids in this player's hand
  score = ndb.IntegerProperty()#current score of this player
  position = ndb.IntegerProperty()#Table position for this player
  alert = ndb.IntegerProperty()
  isCzar = ndb.BooleanProperty()
  lastAction = ndb.DateTimeProperty()
  
  @EndpointsAliasProperty()
  def gameKey(self):
    return ndb.Key('Game', self.gameId)
    
  @EndpointsAliasProperty()
  def gameName(self):
    return self.gameKey.get().gameName
  
  @EndpointsAliasProperty(property_type=messages.IntegerField)
  def gameStatus(self):
    return self.gameKey.get().status
    
  @EndpointsAliasProperty(property_type=messages.IntegerField)
  def currentRound(self):
    return self.gameKey.get().currentRound
  
  @EndpointsAliasProperty()
  def czarName(self):
    czarUser = self.gameKey.get().czar.get().user
    return UserInfo.query(UserInfo.user==czarUser).get().alias
  
  @EndpointsAliasProperty(property_type=messages.BooleanField)
  def userSubmitted(self):
    submissionQuery = Submission.query(Submission.playerKey==self._key, Submission.status!=SUBMISSION_STATUS_COMPLETE)
    
    return (submissionQuery.count() > 0)
  
  @EndpointsAliasProperty(property_type=messages.IntegerField)
  def subsNeeded(self):
    submissionQuery = Submission.query(Submission.gameId==self.gameId, Submission.status != SUBMISSION_STATUS_COMPLETE)
    
    return self.gameKey.get().maxPlayers - submissionQuery.count() - 1
  
  @EndpointsAliasProperty(property_type=messages.IntegerField)
  def blackCardId(self):
    return self.gameKey.get().currentBlack
  
  @EndpointsAliasProperty()
  def userAlias(self):
    return UserInfo.query(UserInfo.user==self.user).get().alias
  
  @EndpointsAliasProperty(property_type=messages.BooleanField)
  def success(self):
    return True
  
  @EndpointsAliasProperty(property_type=messages.IntegerField, repeated=True)
  def submissionIds(self):
    submission = Submission.query(Submission.playerKey==self._key, Submission.status!=SUBMISSION_STATUS_COMPLETE).get()
    
    if(submission is None):
      return []
    
    return submission.whiteCardIds
  
  
#Previous round information.  Contains information for one round of the ancestor game.
class PastRound(EndpointsModel):
  gameId = ndb.IntegerProperty()#Game with which this round is associated
  roundNumber = ndb.IntegerProperty()#Round number for this round
  blackCardId = ndb.IntegerProperty()
  czar = ndb.UserProperty()#User who was czar in this round
  winner = ndb.UserProperty()#User who won this round
  
  @EndpointsAliasProperty()
  def czarName(self):
    return UserInfo.query(UserInfo.user == self.czar).get().alias
  
  @EndpointsAliasProperty()
  def winnerName(self):
    return UserInfo.query(UserInfo.user == self.winner).get().alias
  
#Game information.  Contains information for a given game.
class Game(EndpointsModel):
  gameName = ndb.StringProperty()#Game name
  status = ndb.IntegerProperty()#Game status - defined above
  host = ndb.UserProperty()#User who is hosting this game
  czar = ndb.KeyProperty()#key of Player who is currently picking
  maxPlayers = ndb.IntegerProperty()#Maximum number of players who can be in this game
  currentRound = ndb.IntegerProperty()#current round number
  currentBlack = ndb.IntegerProperty()#key of current black card
  whiteDeck = ndb.IntegerProperty(repeated=True)#Ids of all white cards left in the deck
  blackDeck = ndb.IntegerProperty(repeated=True)#Ids of all black cards left in the deck
  cardSets = ndb.IntegerProperty(repeated=True)#Ids of all card sets being used in this game
  
  def setCardSets(self, value):
    self.cardSets = json.loads(value)
    
  @EndpointsAliasProperty(setter=setCardSets)
  def cardSetsJson(self):
    return json.dumps(self.cardSets)
  
  @EndpointsAliasProperty(property_type=messages.BooleanField)
  def success(self):
    return True
  
  @EndpointsAliasProperty(repeated=True)
  def players(self):
    playerList = Player.query(Player.gameId == self.id).fetch()
    
    userList = [player.user for player in playerList]
    
    userInfoList = UserInfo.query(UserInfo.user.IN(userList))
    
    return [userInfo.alias for userInfo in userInfoList]
  
  @EndpointsAliasProperty(property_type=messages.BooleanField)
  def userIsHost(self):
    return endpoints.get_current_user() == self.host
  
  @EndpointsAliasProperty()
  def currentUser(self):
    return endpoints.get_current_user().nickname()
    
#One player's submission for a given round
class Submission(EndpointsModel):
  gameId = ndb.IntegerProperty()#Id of the game with which this submission is associated
  playerKey = ndb.KeyProperty()#Key of the player with which this submission is associated
  status = ndb.IntegerProperty()#Submission status - defined above
  roundNumber = ndb.IntegerProperty()#What round number this submission is for
  whiteCardIds = ndb.IntegerProperty(repeated=True)#Cards submitted
  
  @EndpointsAliasProperty()
  def userAlias(self):
    return UserInfo.query(UserInfo.user == self.playerKey.get().user).get().alias
  
  @EndpointsAliasProperty()
  def gameKey(self):
    return ndb.Key('Game', self.gameId)
  
  def setWhiteCardIds(self, value):
    self.whiteCardIds = json.loads(value)
    
  @EndpointsAliasProperty(setter=setWhiteCardIds)
  def whiteCardIdsJson(self):
    return json.dumps(self.whiteCardIds)
  
  @EndpointsAliasProperty(property_type=messages.BooleanField)
  def success(self):
    return True
  
class WhiteCard(EndpointsModel):
  idNum = ndb.IntegerProperty()
  text = ndb.StringProperty()
  cardSetId = ndb.IntegerProperty()
  
class BlackCard(EndpointsModel):
  idNum = ndb.IntegerProperty()
  text = ndb.StringProperty()
  draw = ndb.IntegerProperty()
  pick = ndb.IntegerProperty()
  cardSetId = ndb.IntegerProperty()

class CardSet(EndpointsModel):
  idNum = ndb.IntegerProperty()
  name = ndb.StringProperty()
  description = ndb.StringProperty()

@endpoints.api(name='cah', 
	       version='v1', 
	       description='Cards Against Humanity API', 
	       audiences=[endpoints.API_EXPLORER_CLIENT_ID],
	       allowed_client_ids=[WEB_CLIENT_ID, ANDROID_CLIENT_ID, endpoints.API_EXPLORER_CLIENT_ID]
	       )
class CahApi(remote.Service):
  
  @UserInfo.method(request_fields=('alias', ), 
		   response_fields=('id', ), 
		   path="insertUserInfo",
		   user_required=True,
		   http_method="POST", 
		   name="userInfo.insert")
  def UserInsert(self, newUser):
    newUser.user = endpoints.get_current_user()
    
    userQuery = UserInfo.query(UserInfo.user == newUser.user).get(keys_only=True)
    
    if(userQuery is not None):
      return userQuery.get()
    
    if(newUser.alias is None):
      newUser.alias = newUser.user.nickname()
      
    newUser.put()
    
    return newUser
  
  @UserInfo.method(request_fields=('alias', 'regId', ),
		   response_fields=('success', ),
		   http_method="POST",
		   name="userInfo.set",
		   path="setUserInfo/{id}")
  def SetUserInfo(self, userInfo):
    if(not userInfo.from_datastore):
      raise endpoints.NotFoundException("User Not Found")
    
    userInfo.put()
    
    return userInfo
  
  @UserInfo.method( http_method="GET",
		    name="userInfo.get",
		    path="getUserInfo/{id}",
		    request_fields=('id', ),
		    response_fields=('regId', 'alias', ))
  def GetUserInfo(self, userInfo):
    if(not userInfo.from_datastore):
      raise endpoints.NotFoundException("User not found")
    
    return userInfo
  
  @Game.method(request_fields=('gameName', 'maxPlayers', 'cardSetsJson', ), 
	       response_fields=('id', ),
	       user_required=True,
	       http_method="POST", 
	       name="game.create",
	       path="createGame")
  def CreateGame(self, newGame):
    currentUser = endpoints.get_current_user()
    user = UserInfo.query(UserInfo.user == currentUser).get(keys_only=True)
    
    if(user is None):
      raise endpoints.BadRequestException("User does not exist")
    
    newGame.host = currentUser
    newGame.currentRound = 1
    newGame.submissions = []
    newGame.status = 0
    blackDeck = BlackCard.query(BlackCard.cardSetId.IN(newGame.cardSets)).fetch()
    whiteDeck = WhiteCard.query(WhiteCard.cardSetId.IN(newGame.cardSets)).fetch()
    
    random.shuffle(blackDeck)
    random.shuffle(whiteDeck)
    
    newGame.blackDeck = [blackCard.idNum for blackCard in blackDeck]
    newGame.whiteDeck = [whiteCard.idNum for whiteCard in whiteDeck]
    
    gameKey = newGame.put()
    
    player = Player()
    player.gameId = gameKey.id()
    player.user = currentUser
    player.hand = []
    player.score = 0
    player.position = -1
    player.alert = NO_ALERTS
    player.isCzar = False
    
    player.put()
    
    return newGame
  
  @Game.method(user_required=True,
	       request_fields=('id', ),
	       response_fields=('success', ),
	       http_method="DELETE",
	       name="game.cancel",
	       path="cancelGame/{id}")
  def CancelGame(self, game):
    if not game.from_datastore:
      raise endpoints.NotFoundException("Game not found")
    
    if not game.host == endpoints.get_current_user():
      raise endpoints.ForbiddenException("You are not the host of this game")
    
    query = Player.query(Player.gameId == game._key.id())
    ndb.delete_multi(query.fetch(keys_only=True))
    
    game._key.delete()
    return game
  
  @Player.method(response_fields=('success', ),
		 request_fields=('gameId', ),
		 user_required=True,
		 http_method="POST",
		 name="game.join",
		 path="joinGame/{gameId}")
  def JoinGame(self, player):
    currentUser = endpoints.get_current_user()
    
    query = Player.query(Player.gameId == player.gameId, Player.user == currentUser)
    
    if(query.get(keys_only=True)):
      raise endpoints.ForbiddenException("You are already in this game.")
    
    game = player.gameKey.get()
    
    if(game is None):
      raise endpoints.NotFoundException("Game not found")
    
    players = Player.query(Player.gameId == player.gameId)
    
    if(game.status != GAME_STATUS_PENDING or (players.count() == game.maxPlayers)):
      raise endpoints.BadRequestException("Game %s is not currently accepting new players" % game.gameName)
    
    player.user = currentUser
    player.hand = []
    player.score = 0
    player.position = -1
    player.alert = NO_ALERTS
    player.isCzar = False
    
    player.put()
    
    return player
  
  @Game.method(request_fields=('id', ),
	       path="leaveGame/{id}",
		 user_required=True,
		 response_fields=('success', ),
		 http_method="POST",
		 name="game.leave")
  def LeaveGame(self, game):
    if not game.from_datastore:
      raise endpoints.NotFoundException("Game not found")
    
    if(game.status != GAME_STATUS_PENDING):
      raise endpoints.ForbiddenException("You cannot leave a game after it has started")
    
    currentUser = endpoints.get_current_user()
    
    if(game.host == currentUser):
      raise endpoints.ForbiddenException("Host cannot leave the game")
    
    player = Player.query(Player.user == currentUser, Player.gameId == game.id).get(keys_only=True)
    
    if(player is None):
      raise endpoints.NotFoundException("You are not in this game")
    
    player.delete()
    
    return game
  
  @Game.method(request_fields=("id", ),
	       response_fields=("success", ),
	       path="startGame/{id}",
	       user_required=True,
	       name="game.start",
	       http_method="POST")
  def StartGame(self, game):
    if(not game.from_datastore):
      raise endpoints.NotFoundException("Game not found")
    
    if(game.status != GAME_STATUS_PENDING):
      raise endpoints.BadRequestException("Game %s is not pending" % game.gameName)
    
    currentUser = endpoints.get_current_user()
    
    if(currentUser != game.host):
      raise endpoints.ForbiddenException("You are not the host of game %s" % game.gameName)
    
    playerQuery = Player.query(Player.gameId==game.id)
    
    if(playerQuery.count() != game.maxPlayers):
      raise endpoints.BadRequestException("Game %s is not full yet" % game.gameName)
    
    blackDeck = game.blackDeck
    game.currentBlack = blackDeck.pop()
    game.blackDeck = blackDeck
    game.status = 1
    
    currentBlackCard = BlackCard.query(BlackCard.idNum==game.currentBlack).get()
    
    draw = 10 + currentBlackCard.draw
    
    positions = range(game.maxPlayers)
    random.shuffle(positions)
    
    i=0
    players = playerQuery.fetch()
    
    whiteDeck = game.whiteDeck
    
    users = []
    for player in players:
      player.position = positions[i]
      player.alert = 1
      if(player.user != currentUser):
	users += [player.user]
      if(positions[i]==0):
	game.czar = player._key
	player.alert = 0
	player.isCzar = True
      i+=1
      whiteDeck = CahApi.drawWhites(self, player, draw, whiteDeck)
    
    game.whiteDeck = whiteDeck
    game.put()
    
    CahApi.sendAlertNotification(self, users, game)
    
    return game
  
  @Submission.method(request_fields=('whiteCardIdsJson', ),
		     path="submitWhite/{gameId}",
		 user_required=True,
		 response_fields=('success', ),
		 http_method="POST",
		 name="white.submit")
  def SubmitWhite(self, submission):
    game = submission.gameKey.get()
    
    if(game is None):
      raise endpoints.NotFoundException("Game not found")
    
    if(game.status != GAME_STATUS_WAITING_SUBMITS):
      raise endpoints.BadRequestException("Game %s is not accepting submissions" % game.gameName)
    
    playerKey = Player.query(Player.user==endpoints.get_current_user(), Player.gameId==submission.gameId).get(keys_only=True)
    
    if(playerKey is None):
      raise endpoints.ForbiddenException("You are not in game %s" % game.gameName)
    
    if(playerKey == game.czar):
      raise endpoints.ForbiddenException("You are currently picking")
    
    submissionQuery = Submission.query(Submission.status==SUBMISSION_STATUS_PENDING)
    
    subsIn = submissionQuery.count()
    
    if(subsIn == game.maxPlayers-1):
      raise endpoints.ForbiddenException("You have already submitted")
    
    if(submissionQuery.filter(Submission.playerKey == playerKey).count() != 0):
      raise endpoints.ForbiddenException("You have already submitted")
    
    player = playerKey.get()
    
    if(not set(submission.whiteCardIds).issubset(player.hand)):
      raise endpoints.BadRequestException("You do not have all of these cards")
    
    blackCard = BlackCard.query(BlackCard.idNum==game.currentBlack).get()
    
    if(blackCard.pick != len(submission.whiteCardIds)):
      raise endpoints.BadRequestException("Need %i cards.  Found %i" % (blackCard.pick, len(submission.whiteCardIds)))
    
    submission.playerKey = playerKey
    submission.status = SUBMISSION_STATUS_PENDING
    submission.roundNumber = game.currentRound
    
    submission.put()
    
    player = playerKey.get()
    hand = player.hand
    player.hand = list(set(hand) - set(submission.whiteCardIds))
    player.put()
    
    subsIn += 1
    
    if(subsIn == game.maxPlayers - 1):
      czarPlayer = game.czar.get()
      czarPlayer.alert = 1
      czarPlayer.put()
      
      game.status = GAME_STATUS_WAITING_CZAR
      game.put()
      
      CahApi.sendAlertNotification(self, [czarPlayer.user], game)
      
      submissions = Submission.query(Submission.gameId == submission.gameId, Submission.status == SUBMISSION_STATUS_PENDING).fetch()
      
      for sub in submissions:
	sub.status = SUBMISSION_STATUS_ACTIVE
	sub.put()
      
    return submission
  
  @Submission.method(request_fields = ('id', ),
		 response_fields= ('success', ),
		 user_required = True,
		 http_method="POST",
		 name="winner.pick",
		 path="pickWinner/{id}")
  def PickWinner(self, submission):
    if not submission.from_datastore:
      raise endpoints.NotFoundException("Submission not found")
    
    if submission.status != SUBMISSION_STATUS_ACTIVE:
      raise endpoints.BadRequestException("Submission not active")
    
    game = submission.gameKey.get()
    
    if game is None:
      raise endpoints.NotFoundException("Game not found")
    
    if game.status != GAME_STATUS_WAITING_CZAR:
      raise endpoints.BadRequestException("Game not accepting picks")
    
    czar = game.czar.get()
    
    if czar.user != endpoints.get_current_user():
      raise endpoints.ForbiddenException("You are not the czar")
    
    currentCzarPosition = czar.position
    newCzarPosition = currentCzarPosition + 1
    if(newCzarPosition == game.maxPlayers):
      newCzarPosition = 0
    
    winner = submission.playerKey.get()
    winner.score = winner.score + 1
    winner.put()
    
    pastRound = PastRound()
    pastRound.gameId = game.id
    pastRound.roundNumber = game.currentRound
    pastRound.blackCardId = game.currentBlack
    pastRound.czar = czar.user
    pastRound.winner = winner.user
    
    pastRound.put()
    
    activeSubmissions = Submission.query(Submission.status == SUBMISSION_STATUS_ACTIVE).fetch()
    
    for submission in activeSubmissions:
      submission.status = SUBMISSION_STATUS_COMPLETE
      submission.put()
    
    blackDeck = game.blackDeck
    game.currentBlack = blackDeck.pop()
    game.blackDeck = blackDeck
    game.currentRound = game.currentRound + 1
    
    currentBlackCard = BlackCard.query(BlackCard.idNum == game.currentBlack).get()
    
    extraDraw = currentBlackCard.draw
    
    players = Player.query(Player.gameId == game.id).fetch()
    
    whiteDeck = game.whiteDeck
    
    users = []
    for player in players:
      player.alert = 1
      draw = 10 - len(player.hand)
      
      if(player.position == newCzarPosition):
	game.czar = player._key
	player.isCzar = True
      else:
	draw += extraDraw
	player.isCzar = False
	
	if(player.user != endpoints.get_current_user()):
	  users += [player.user]
	  
      if(draw > 0):
	whiteDeck = CahApi.drawWhites(self, player, draw, whiteDeck)
      
      
      player.put()
    
    game.status = GAME_STATUS_WAITING_SUBMITS
    game.put()
    
    #CahApi.sendAlertNotification(self, users, game)
    
    return submission
  
  @Player.query_method(user_required=True,
		       collection_fields=('gameId', 'gameName', 'gameStatus', 'alert', ),
		       name="currentGames.fetch",
		       http_method="GET",
		       path="fetchCurrentGames")
  def FetchCurrentGames(self, query):
    return query.filter(Player.user == endpoints.get_current_user())
  
  @Game.query_method(name="pendingGames.fetch",
		     collection_fields=('id', 'gameName', ),
		     http_method="GET",
		     path="fetchPendingGames")
  def FetchPendingGames(self, query):
    query = query.filter(Game.status == GAME_STATUS_PENDING)
    
    return query
  
  @Game.method(name="pendingGameInfo.fetch",
		request_fields=('id', ),
		user_required=True,
		response_fields=('userIsHost', 'gameName', 'maxPlayers', 'players', 'currentUser', ),
		http_method="GET",
		path="fetchPendingGameInfo/{id}")
  def FetchPendingGameInfo(self, game):
    if(not game.from_datastore):
      raise endpoints.NotFoundException("Game not found")
    
    return game
  
  @Player.query_method(name="players.fetch",
		       path="fetchPlayers/{gameId}",
		       query_fields=('gameId', ),
		       collection_fields=('id', 'userAlias', ),
		       http_method="GET")
  def FetchGamePlayers(self, query):
    return query
  
  @Player.query_method(user_required=True,
		       query_fields=('gameId', ),
		       collection_fields=('currentRound', 'czarName', 'isCzar', 'userSubmitted', 'subsNeeded', 'blackCardId', 'gameName', 'hand', 'submissionIds', ),
		       http_method="GET",
		       name="activeGameInfo.fetch",
		       path="fetchActiveGameInfo/{gameId}")
  def FetchActiveGameInfo(self, query):
    myQuery = query.filter(Player.user == endpoints.get_current_user())
    
    if(myQuery.count() == 0):
      raise endpoints.NotFoundException("You are not in this game")
    
    game = myQuery.get().gameKey.get()
    if(game is None):
      raise endpoints.NotFoundException("Game does not exist")
    
    if(game.status != GAME_STATUS_WAITING_SUBMITS and game.status != GAME_STATUS_WAITING_CZAR):
      raise endpoints.NotFoundException("Game is not active")
    
    return myQuery
  
  @Submission.query_method(query_fields=('gameId', 'status', ),
			   collection_fields=('id', 'whiteCardIds', ),
			   http_method="GET",
			   name="currentSubmissions.fetch",
			   path="fetchCurrentSubmissions/{gameId}")
  def FetchCurrentSubmissions(self, query):
    return query
  
  @PastRound.query_method(query_fields=('gameId', 'limit', 'order', 'pageToken', ),
			  collection_fields=('roundNumber', 'blackCardId', 'czarName', 'winnerName', ),
			  http_method="GET",
			  name="pastRounds.fetch",
			  path="fetchPastRounds/{gameId}")
  def FetchPastRounds(self, query):
    return query
  
  #limit for this method should be (n-1)*l, where n is the number of players in the game and l is the limit from the above method
  @Submission.query_method(query_fields=('gameId', 'status', 'limit', 'order', 'pageToken', ),
			   collection_fields=('roundNumber', 'userAlias', 'whiteCardIds', ),
			   http_method="GET",
			   name="pastSubmissions.fetch",
			   path="fetchPastSubmissions/{gameId}")
  def FetchPastSubmissions(self, query):
    return query
  
  @CardSet.query_method(collection_fields=('id', 'idNum', 'name', ),
			query_fields=('order', ),
			http_method="GET",
			name="cardSets.fetch",
			path="fetchCardSets"
			)
  def FetchCardSets(self, query):
    return query
  
  #Draw n white cards for a given player
  #Input: player, n, whiteDeck
  #Output: remaining white cards if successful, false if there are less than n white cards left in the deck
  def drawWhites(self, player, n, whiteDeck):
    if(len(whiteDeck) < n):
      return False
    
    hand = player.hand
    
    for i in range(n):
      hand += [whiteDeck.pop()]
    
    player.hand = hand
    player.put()
    
    return whiteDeck
    
  #Sends a push notification to the mobile device of the selected users alerting them that the game is ready for them to go
  #Input: userKeys, gameKey
  #Output: True if messages were sent successfully, false otherwise
  def sendAlertNotification(self, users, game):
    #headers = {'Content-Type': 'application/json', 'Authorization': API_KEY}
    #message = {}
    
    #userInfos = UserInfo.query(UserInfo.user.IN(users)).fetch()
    #regIds = [userInfo.registrationId for userInfo in userInfos]
    
    ##Filter out None values
    #newRegIds = []
    
    #for regId in regIds:
      #if(regId):
	#newRegIds += [regId]
    
    #regIds = newRegIds
    
    #message["registration_ids"] = regIds
    #message["collapse_key"] = "cah"
    
    #gameName = game.gameName
    #data = {}
    #data["gameKey"] = game._key.urlsafe()
    #data["gameName"] = gameName
    #data["type"] = "alert"
    #message["data"] = data
    
    #result = urlfetch.fetch(url=GCM_URL, payload=json.dumps(message), method=urlfetch.POST, headers=headers)
    #return result.status_code
    return

application = endpoints.api_server([CahApi], restricted=False)