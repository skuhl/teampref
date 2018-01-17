#!/usr/bin/env python3

from random import shuffle
import random
import copy
import signal
import sys
import math
import os,csv


# A person's pain change by this amount for every friend that is on
# their team. I.e., if two of Jane's friends are on her team, then her
# pain will change by confiPainFriend*2.
configPainFriend = -1

# A person's pain will increase by this amount for every foe that is
# on their team. I.e., if two of Jane's foes are on her team, then her
# pain will increase by configPainFoe*2.
configPainFoe = 10


# If a team must have people that satisfy 3 traits, but 2 of those
# traits are not satisfied, then the pain of everybody on the team
# will increase by configPainTrait*2.
configPainTrait = 3


def dedupList(oldlist):
    """Remove duplicate entries in a list while preserving order
    (first entry is kept, subsequent entries removed.)"""
    newlist = []
    for i in oldlist:
        if i not in newlist:
            newlist.append(i)
    return newlist

class PainIndex:
    """A PainIndex class defines an overall pain for a group of
    teams. Every team arrangement we try will produce a PainIndex. This
    class provides comparators so we can easily compare two pain indices
    and identify which is larger. It also provides an easy way to print
    out the current overall pain values."""
    def __init__(self, highestPain, numPeopleWithHighest, avgPain):
        self.highestPain = highestPain
        self.numPeopleWithHighest = numPeopleWithHighest
        self.avgPain = avgPain

    def __str__(self):
        return "%d,%d,%0.2f" % (self.highestPain, self.numPeopleWithHighest, self.avgPain)


    def __lt__(self, otherScore):
        if self.highestPain < otherScore.highestPain:
            return True
        if self.highestPain == otherScore.highestPain and self.numPeopleWithHighest < otherScore.numPeopleWithHighest:
            return True
        if self.highestPain == otherScore.highestPain and self.numPeopleWithHighest == otherScore.numPeopleWithHighest and self.avgPain < otherScore.avgPain:
            return True
        return False

    def __eq__(self, otherScore):
        if self.highestPain == otherScore.highestPain and self.numPeopleWithHighest == otherScore.numPeopleWithHighest and self.avgPain == otherScore.avgPain:
            return True
        return False


class Person:

    def __init__(self, name, prefs, friends, foes, traits):
        # Save names, team preferences, friends, foes, and traits in lowercase.
        self.name    = name.lower().strip()
        self.prefs   = dedupList([x.lower().strip() for x in prefs])
        self.friends = dedupList([x.lower().strip() for x in friends])
        self.foes    = dedupList([x.lower().strip() for x in foes])
        self.traits  = dedupList([x.lower().strip() for x in traits])

        # This will be set to true if this person is assigned to the
        # unassigned team list. It means that they are a free agent (even
        # if we temporarily assign them to a team).
        self.freeAgent = False

        # ---
        # The following info is used to optimize performance.

        # A hash of the name. The Team class uses a set of hashes of
        # people on the team to speed up checks of if the person is on
        # the team or not.
        self.namehash = hash(self.name)

        # Foe names hashed and stored in a set
        self.foeset = frozenset([ hash(f) for f in self.foes ])
        # Friend names hashed and stored in a set
        self.friendset = frozenset([ hash(f) for f in self.friends])

        # Dictionary of team preferences. Allows us to quickly
        # translate from team name to the rank of the preference.
        self.prefdict = { }
        for i in range(len(self.prefs)):
            self.prefdict[self.prefs[i]] = i
            
    def hasTrait(self, trait):
        # Checks if person has the given trait.
        for t in self.traits:
            if t == trait:
                return True
        return False

    def painIndex(self, team):
        """Calculates the pain index for the individual if they are on the
specified team. Note that this does not tell you anything about if
other people's pain would increase if they were on the specified
team."""
        
        painIndex = 0
        if team.name in self.prefdict:
            # Calculate pain based on this person's team preferences.
            painIndex = self.prefdict[team.name]
        else:
            # If we are on a team we didn't specify as a preference...
            painIndex = len(self.prefs)

        friendsPresent = team.nameset & self.friendset
        foesPresent    = team.nameset & self.foeset

        return painIndex + configPainFoe*len(foesPresent) + configPainFriend*len(friendsPresent) + team.traitPain()
        #return painIndex

        
class Team:

    def __init__(self, name, capacity, needTraits):
        self.name = name.lower()
        if capacity < 1:
            print("ERROR: Capacity of team %s was too small (%d) to have teammembers.\n" % ( self.name, capacity) )
            exit(1)
            
        self.capacity = capacity
        self.people = []
        self.nameset = set()
        # *Dictionary* containing traits and counts that we need (convert to lowercase)
        self.traits = {}
        if needTraits:
            for trait, value in needTraits.items():
                self.traits[trait.lower()] = value
        
        # Dictionary containing count of traits that we have
        self.currentTraits = {}

    def traitCount(self, trait):
        """How many people on this team have this trait?"""
        if trait in self.currentTraits:
            return self.currentTraits[trait]
        else:
            return 0


    def traitPain(self):
        """Calculate how the pain for this team should be adjusted based on if
all of the required traits are satisfied or not."""
        # Count how many needed traits are unfilled
        unfilledCount = 0
        for trait, value in self.unfilledTraits().items():
            unfilledCount = unfilledCount+value

        # # If a trait isn't needed, try to group those with similar traits together.
        # sameTraits = 0
        # for trait, value in self.currentTraits.items():
        #     # If trait is not a needed trait
        #     if trait not in self.traits:
        #         sameTraits = sameTraits+value-1
        #         #print("%s %d" % (trait, sameTraits) )
        # return unfilledCount*configPainTrait - sameTraits*2
                
        return unfilledCount*configPainTrait


        
    def unfilledTraitCount(self):
        """Count how many traits on this team remain unfilled."""
        traits = self.unfilledTraits()
        count = 0
        for trait, value in traits.items():
            count = count+value
        return count
        
    def unfilledTraits(self):
        """Return a dictionary containing the traits that are unfilled and the number of slots per trait that remain open."""
        unfilledTraits = {}

        # For each trait our team needs
        for trait in self.traits:
            shortfall = self.traits[trait] - self.traitCount(trait)
            if shortfall > 0:
                unfilledTraits[trait] = shortfall
            
        return unfilledTraits

        
    def hasPersonNamed(self, name):
        """Checks if a name matches someone already on the team."""
        return hash(name) in self.nameset
    
        #for person in self.people:
        #    if person.name == name:
        #        return True
        #return False

    def hasPerson(self, person):
        """Checks if a person is on the team."""
        return person.namehash in self.nameset

    def addPerson(self, person):
        """Adds a person to the team if there is room and if they are not already on the team."""
        if self.hasRoom() and not self.hasPerson(person):
            self.people.append(person)
            self.nameset.add(person.namehash)

            # If person has traits, iterate over all traits and add
            # them to the teams' traits.
            if person.traits:
                for trait in person.traits:
                    if trait in self.currentTraits:
                        self.currentTraits[trait] = self.currentTraits[trait] + 1
                    else:
                        self.currentTraits[trait] = 1
                
            # print("'%s' added to team '%s'" % (person.name, self.name))
            return True
        return False

    def removePerson(self, person):
        #print("Removing %s" % person.name)
        self.people.remove(person)
        self.nameset.discard(hash(person.name))
        if person.traits:
            for trait in person.traits:
                self.currentTraits[trait] = self.currentTraits[trait]-1

    
    def containsFoeOf(self, person):
        """Does someone already on the team list this person as a foe?"""
        if self.size() == 0:
            return False

        for p in self.people:
            if person.namehash in p.foeset:
                return True
        return False

    def containsFriendOf(self, person):
        """Does someone already on the team list this person as a friend?"""
        if self.size() == 0:
            return 0

        numFriends=0
        for p in self.people:
            if person.namehash in p.friendset:
                numFriends = numFriends+1
        return numFriends
    

    def painList(self):
        """Return a list of pain values, one for each person on team."""
        return [ x.painIndex(self) for x in self.people ]
    
    
    def painMax(self):
        """Calculates the pain index for each person and returns the largest index"""
        painList = self.painList()
        if len(painList) > 0:
            return max(painList)
        else:
            return -1000

    def painAvg(self):
        painList = self.painList()
        if len(painList) > 0:
            return float(sum(painList))/len(painList)
        else:
            return -1000

    def size(self):
        """Number of people on the team."""
        return len(self.people)

    def hasRoom(self):
        """Returns true if more people can be assigned to team."""
        return len(self.people) < self.capacity

    def roomRemain(self):
        remain = self.capacity - len(self.people)
        if remain < 0:
            return 0
        else:
            return remain

    def sanityCheck(self):
        if len(self.nameset) != len(self.people):
            print("Team sanity check: nameset didn't match list of people.")
            sys.exit(1)
            
        for p in self.people:
            if hash(p.name) not in self.nameset:
                print("Team sanity check: hash of name was not in nameset.")
                sys.exit(1)
            
        # TODO: Verify that team's unfilled traits match based on the
        # people who are on the team.
        


    def __str__(self):
        s = ""
        s = "Team: '%s' (capacity %d, size %d, painMax %d, painAvg %0.2f, missingTraits %d):\n" % ( self.name, self.capacity, self.size(), self.painMax(), self.painAvg(), self.unfilledTraitCount() )

        for trait in self.traits:
            teamHas = self.traitCount(trait)
            teamNeeds = self.traits[trait]
            shortfall = teamNeeds-teamHas
            s = s+"Trait '%s': team has %d, team needs %d, shortfall %d\n" % (trait, self.traitCount(trait), self.traits[trait], shortfall)


        # Sort people alphabetically
        self.people.sort(key=lambda x: x.name)
        
        for i in self.people:
            if self.name in i.prefdict:
                rank = "rank %d" % i.prefdict[self.name]
            else:
                rank = "rank -"

            friends = "%d/%d friends" % (len(self.nameset & i.friendset), len(i.friendset))
            foes    = "%d/%d foes"    % (len(self.nameset & i.foeset),    len(i.foeset))
            
            s = s+"%s (pain %d, %s, %s, %s, traits %s)\n" % (i.name, i.painIndex(self), rank, friends, foes, i.traits)
        return s

    def __hash__(self):
        return hash(self.name)
    

class TeamGroup:
    def __init__(self):
        self.teams = []       # A list of teams
        self.unassigned = []  # A list of people without team assignments

    def numUnassigned(self):
        return len(self.unassigned)

    def addUnassigned(self, person):
        """Add a person to the unassigned list."""
        person.freeAgent = True
        self.unassigned.append(person)

    def reset(self, percentage, removePainAbove=1000):
        """Removes percentage of free agents and puts them
back into unassigned list. If the person's pain is above
removePainAbove, then always remove them."""
        
        for t in self.teams:
            # Maintain list of those that are free agents and those that are not.
            free = []
            # Always remove people with high pain. Otherwise, remove
            # people based on percentage.
            for p in t.people:
                if p.freeAgent and (p.painIndex(t) > removePainAbove or random.random() < percentage/100.0):
                    free.append(p)
                    t.removePerson(p)

            # Add free agents to unassigned list, keep those who are
            # not free on the team.
            self.unassigned = self.unassigned + free

        # Occasionally run sanity check
        if random.random() < .001:
            self.sanityCheck()

    def sanityCheck(self, checkForMissing=False):
        for t in self.teams:
            t.sanityCheck()

        # Get a list of all people (unassigned and assigned to teams)
        allPeople = self.unassigned
        for t in self.teams:
            allPeople = allPeople + t.people

        if checkForMissing:
            # Verify the friends/foes/team preferences for the person are valid
            for p in allPeople:
                for other in p.friends + p.foes:
                    if not self.personExists(other):
                        print("Person '%s' lists '%s' as a friend/foe but the friend/foe doesn't exist." % (p.name, other))
                        #exit(1)
                for t in p.prefs:
                    if not self.findTeam(t):
                        print("Person '%s' lists '%s' as a team preference, but the team doesn't exist." % (p.name, t))
                        exit(1)
            


                      
    def makeAssignments(self, obeyPrefs):
        """Put all unassigned people onto teams."""

        # Randomize ordering of unassigned people
        shuffle(self.unassigned)

        # While there are unassigned people, assign them according to their preferences.
        failList = []
        while len(self.unassigned) > 0:
            person = self.unassigned.pop()  # remove person from end of list
            if not self.addPersonPrefs(person, obeyPrefs):
                failList.append(person)

        self.unassigned = failList

    def addTeam(self, team):
        """Add a new team to the team group."""
        if self.findTeam(team.name) == None:
            self.teams.append(team)
        else:
            print("ERROR: Team '%s' was already in team group." % team.name)
        

    def findTeam(self, teamName):
        """Find the team with the given team name."""
        for t in self.teams:
            if t.name.lower() == teamName.lower():
                return t
        return None

    def randomTeam(self):
        """Return a random team. Useful when randomly assigning preferences to randomly generated people."""
        return random.choice(self.teams)
    
    def randomTeams(self, count):
        """Return a random team. Useful when randomly assigning preferences to randomly generated people."""
        teams = []
        while len(teams) < count:
            candidate = random.choice(self.teams)
            if candidate not in teams:
                teams.append(candidate)
        return teams
    
    def personExists(self, name):
        """Verifies that someone with the person's name exists on either a team or on the unassigned list. This function helps us verify that a listed friend/foe actually exists after we load the data."""
        h = hash(name)
        for t in self.teams:
            if h in t.nameset:
                return True
        for p in self.unassigned:
            if name == p.name:
                return True
        return False


    
    def addPersonToTeam(self, person, teamName):
        """Add a person to the specified team based on the team name. Return True if successful. Exit if we can't find the team."""
        team = self.findTeam(teamName)
        if team:
            return team.addPerson(person)
        else:
            print("ERROR: Trying to add person '%s' to team '%s', but it doesn't exist" % (person.name, teamName))
            exit(1)

        
    def addPersonPrefs(self, person, obeyPrefs):
        """Try to add a person in onto a mostly optimal team."""

        # Calculate pain index for the person if we were to place him on each team.
        tp = [] # (team, pain, roomRemain) tuples

        for t in self.teams:
            if not t.hasRoom():
                continue

            # There are two competing interests when we place a
            # person: The person's pain and the pain of the team which
            # we might add the person to. We primarily focus on the
            # person's preferences, but there is one case were we
            # consider the team's preferences: We don't want to add a
            # person onto the team that is a foe of someone who is
            # already on the team.
            pain = person.painIndex(t)
            if t.containsFoeOf(person):
                pain = pain+configPainFoe

            # Adjust pain based on how this new person might help fill traits
            traitsWeFill = 0
            for trait, value in t.unfilledTraits().items():
                if person.hasTrait(trait):
                    traitsWeFill = traitsWeFill+1
            pain = pain - traitsWeFill*configPainTrait
            

            # Keep track of the team, pain of the person we'd add onto
            # the team, and the amount of room on the team.
            tp.append( (t, pain, t.roomRemain()) )

        # Shuffle the order of teams in place. We do this step to help
        # randomize the subsequent sort() function so that if there
        # are two teams which have equal pain and capacity, we don't
        # always pick the same one.
        shuffle(tp)
      
        # Sort possible teams to join by pain. If there are two good
        # teams that we could be added to, prioritize joining the
        # group with the most room available to keep more options
        # available for the next person.
        tp.sort(key=lambda tup: (tup[1], tup[2]))

#        print()
#        for tup in tp:
#            print("%s %d %d" % (tup[0].name, tup[1], tup[2]))


        # Add them to the team, starting with the best option. Don't
        # always do so, however, so that we can explore alternative
        # options sometimes.
        for tup in tp:
            if random.random() < obeyPrefs/100.0 and tup[0].addPerson(person):
                return True

        # If that didn't work, actually try adding the person to each
        # team one at a time until one succeeds. This is necessary
        # because we may have skipped some teams that have room
        # because of the randomness we inserted (via obeyPrefs).
        for t in self.teams:
            if t.addPerson(person):
                return True
            
        print("WARNING: No space available for person (%s)." % person.name)
        return False

    def painMax(self):
        """Return the largest pain index among all teams."""
        teamPains = [ t.painMax() for t in self.teams ]
        if len(teamPains) > 0:
            return max(teamPains)
        else:
            return -1000

    def painIndex(self):
        """Since many solutions may have the same max pain, we use fractional part of the index value to represent how many people have the largest pain."""

        # Get the individual team pains (each team pain is a list of
        # individual pain)
        teamPains = [ t.painList() for t in self.teams ]

        # Collapse list of lists into a list
        singleList = [item for sublist in teamPains for item in sublist]

        if len(singleList) == 0:
            return -1000
        
        largestPain = max(singleList)
        numWithLargestPain = singleList.count(largestPain)

        # Return the largest team value
        return PainIndex(largestPain, numWithLargestPain, sum(singleList)/float(len(singleList)))
        # return largestPain + numWithLargestPain/1000.0
        
        
    def __str__(self):
        s = ""
        for t in self.teams:
            s = s + str(t) + "\n"
        return s

    def writeFile(self, filename="output.csv"):
        with open(filename, "w") as csvfile:
            writer = csv.writer(csvfile)

            writer.writerow(["Name", "Team Name", "Team preferences", "Friends", "Foes", "Traits"])
            
            for team in self.teams:
                for p in team.people:

                    prefs   = ",".join(p.prefs)
                    friends = ",".join(p.friends)
                    foes    = ",".join(p.foes)
                    traits  = ",".join(p.traits)
                        
                    writer.writerow([p.name, team.name, prefs,
                                     friends, foes, traits])

    

class TeamMutate:
    """A set of possible solutions which we will try modifying to find even better solutions."""
    
    def __init__(self, teamGroup, numStrains):
        self.tg = []     # A list of TeamGroups
        self.pain = []   # Pain associated with each TeamGroup

        teamGroup.reset(100)
        
        for i in range(numStrains):
            self.tg.append(copy.deepcopy(teamGroup))
            t = self.tg[i]
            t.makeAssignments(99)
            if t.numUnassigned() > 0:
                print("Failed to assign %d people." % t.numUnassigned())
            self.pain.append(t.painIndex())
            print("strain %d has initial pain of %s" % (i, self.pain[i]))

        print("Created %d strains." % numStrains)

    def numStrains(self):
        return len(self.tg)
        
    def mutateStrain(self, generations, strain, q):
        # Iterate the specified number of generations.
        pain = self.pain[strain]
        for gen in range(generations):
            # Make a copy so we don't lose current solution
            working = copy.deepcopy(self.tg[strain])
            # Remove some people from teams
            working.reset(random.randrange(1,100), pain.highestPain-1)
            # Assign people back into teams
            working.makeAssignments(random.random()*20+80)
            # Measure new pain
            pain = working.painIndex()

            # Save new pain if it is less than best so far. If is of
            # equal pain, switch to the new version instead so that we
            # try a wider variety of options.
            if pain == self.pain[strain]:
                self.pain[strain] = pain
                self.tg[strain] = working
            if pain < self.pain[strain]:
                print("strain %d found new best pain %s (previous was %s)" % (strain, pain, self.pain[strain]))
                self.pain[strain] = pain
                self.tg[strain] = working


        if q:
            q.put((strain, self.tg[strain], self.pain[strain]))

            
    def mutate(self, generations):
        if self.numStrains() == 1:
            for i in range(self.numStrains()):
                self.mutateStrain(generations, i, None)
            return


        from multiprocessing import Process
        from multiprocessing import Queue
        threads = []
        queues = []
        for i in range(self.numStrains()):
            q = Queue()
            queues.append(q)
            threads.append(Process(name="child", target=self.mutateStrain, args=[generations, i, q]))
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        for q in queues:
            val = q.get()
            self.tg[val[0]] = val[1]
            self.pain[val[0]] = val[2]
            

    def bestStrain(self):
        bestPain = PainIndex(1000,1000,1000)
        bestIndex = 0
        for i in range(len(self.tg)):
            if self.pain[i] < bestPain:
                bestPain = self.pain[i]
                bestIndex = i

        return (self.tg[bestIndex], self.pain[bestIndex])

    

def generateTeamGroup(numTeams, minSize, maxSize):
    """Create a set of teams with generic names"""
    tg = TeamGroup()
    for i in range(numTeams):
        tg.addTeam(Team("Team%d" % i, random.randint(minSize, maxSize), { "Leader" : 1, "Sound" : 1, "Art" : 1 }))
    return tg

    

def generatePeople(tg, numPeople, numPrefs, numFriends, numFoes):
    """Create a set of people with preferences, friends, and foes. Add them as unassigned people in a team group."""
    
    # Generate names
    peopleNames = []
    for i in range(numPeople):
        peopleNames.append("Person%d" % i)

    # Create preferences, friends, and foes
    for name in peopleNames:
        prefs = []
        friends = []
        foes = []

        # Find some random teams which can be preferences
        teamPrefs = tg.randomTeams(numPrefs)
        for t in teamPrefs:
            prefs.append(t.name)

        # Find some friends (can't be us)
        while len(friends) < numFriends:
            r = random.choice(peopleNames)
            if r != name:
                friends.append(r)

        # Find some foes (can't be us, can't be a friend)
        while len(foes) < numFoes:
            r = random.choice(peopleNames)
            if r != name and r not in friends:
                foes.append(r)

        traits = []
        if random.random() < .3:
            traits.append("Leader")
        if random.random() < .3:
            traits.append("Art")
        if random.random() < .08:
            traits.append("Sound")

        if random.random() < .1:
            traits.append("BonzAI")
            
                
        # Create person and add them as an unassigned person.
        person = Person(name, prefs, friends, foes, traits)
        tg.addUnassigned(person)


def mysplit(string, sep):
    """Tokenize a string. Remove whitespace from tokens. Delete tokens that are empty strings. If sep is none, separate based on whitespace."""

    if not string or len(string) == 0:
        return []
    
    # Append seperator to string. This helps if we are tokenizing a
    # list of items separated by commas and there may (or may not) be
    # a comma at the end of the list.
    if sep:
        string = string+sep
        
    string = string.strip()
    tokens = string.split(sep)
    newtokens = [x.strip() for x in tokens if len(x.strip()) > 0]
    return newtokens
    
        
def readTeamGroup(filename):
    """Read a spreadsheet containing information about teams to create a TeamGroup object."""
    if not os.path.exists(filename):
        print("ERROR: Failed to read file %s\n" % filename)
        exit(1)

    tg = TeamGroup()
    
    with open(filename, "r") as csvfile:
        rows = csv.reader(csvfile)
        if not rows:
            print("ERROR: Failed to read file %s\n" % filename)
            exit(1)
        next(rows, None) # skip first row (header)
            
        for r in rows:
            # print("Working on row: %s\n" % r)
            if len(r) < 2:
                print("Row must have at least 2 columns: %s" % r)
                continue

            teamName = str(r[0])
            maxCapacity = int(r[1])
            if len(r) == 3:
                traits = str(r[2])
            else:
                traits = ""

            # Convert traits into dict:
            traitsDict = {}
            for trait in mysplit(traits, ","):
                tokens = mysplit(trait, None)
                if len(tokens) == 2:
                    traitsDict[str(tokens[0])] = int(tokens[1])
                else:
                    print("ERROR: For team '%s', we expected a quantity after the trait: %s" % (teamName, str(tokens)))
                    exit(1)

            newTeam = Team(teamName, maxCapacity, traitsDict)
            tg.addTeam(newTeam)

    return tg
        

def readPeople(filename, tg):
    """Read people from a spreadsheet and add them to teams (or to the unassigned list)."""
    if not os.path.exists(filename):
        print("ERROR: Failed to read file %s\n" % filename)
        exit(1)

    with open(filename, "r") as csvfile:
        rows = csv.reader(csvfile)
        if not rows:
            print("ERROR: Failed to read file %s\n" % filename)            

        # A set to track which people we have read from the file to
        # ensure file doesn't contain duplicates.
        seenPeople = set()
            
        next(rows, None) # skip first row (header)
        for r in rows:
            #print("Working on row: %s\n" % r)
            if len(r) < 1:
                print("Row must have at least 1 column: %s" % r)
                continue

            personName = str(r[0].strip())
            if personName in seenPeople:
                print("ERROR: Person %s is defined twice in %s." % (personName, filename))
                exit(1)
            else:
                seenPeople.add(personName)
            
            teamName = str(r[1].strip())
            teamPrefs = mysplit(str(r[2]), ",")
            friends   = mysplit(str(r[3]), ",")
            foes      = mysplit(str(r[4]), ",")
            traits    = mysplit(str(r[5]), ",")

            p = Person(personName, teamPrefs, friends, foes, traits)
            if len(teamName) > 0:
                tg.addPersonToTeam(p, teamName.lower().strip())
            else:
                tg.addUnassigned(p)

                
        



# Generate random teams:
# random.seed(233)   # Seed random numbers the same way.
#tg = generateTeamGroup(15, 4, 8)
#generatePeople(tg, 70, 0, 4, 2)

# Read teams/people from files:
tg = readTeamGroup("teams.csv")
readPeople("people.csv", tg)
tg.sanityCheck(checkForMissing=True)

smallestPain = 100000
bestTeamGroup = None

def signal_handler(signal, frame):
    """Handle when Ctrl+C is pressed. Write out best solution sound so far to console and file."""
    import multiprocessing
    if multiprocessing.current_process().name == "child":
        sys.exit(0)
    
    print(str(bestTeamGroup))
    bestTeamGroup.writeFile()
                                    
    print("Smallest pain we saw: %s" % smallestPain)
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# Use a "random" seed for mutation.
import time
random.seed(time.time())
# Create multiple strains using different processes.
mutate = TeamMutate(tg, 8)
while 1:
    # Mutate all strains a specific number of times
    mutate.mutate(300)
    # Identify the strain with the lowest pain.
    bestTeamGroup, smallestPain = mutate.bestStrain()
    print("Best pain for each strain: ")
    painAsStrings = map(str, mutate.pain)
    print(',   '.join(painAsStrings))

    print("Best strain has pain of %s" % smallestPain)
    
