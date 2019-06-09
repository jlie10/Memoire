##############################################################
# EVOLIFE              http://evolife.telecom-paristech.fr   #
# Telecom ParisTech  2018               Jean-Louis Dessalles #
# ---------------------------------------------------------- #
# License:  Creative Commons BY-NC-SA                        #
##############################################################


""" Study of the possibility of self-sacrifice being an ESS
    Simplified base version where Admiration is exogenous
    Serves as base for Sacrifice.py
"""

from random import sample, shuffle, random, choice, randint
from math import exp, log
from time import sleep

import sys
sys.path.append('..')
sys.path.append('../../..')

import Evolife.Ecology.Observer	as EO
import Evolife.Scenarii.Default_Scenario as ED
import Evolife.Ecology.Individual as EI
import Evolife.Ecology.Alliances as EA
import Evolife.QtGraphics.Evolife_Window as EW
import Evolife.QtGraphics.Evolife_Batch  as EB
import Evolife.Ecology.Group as EG
import Evolife.Ecology.Population as EP

from Evolife.Tools.Tools import percent, chances, decrease, error

class Scenario(ED.Default_Scenario):

########################################
#### General initializations and visual display ####
########################################
    def __init__(self):
        # Parameter values
        ED.Default_Scenario.__init__(self, CfgFile='_Params.evo')	# loads parameters from configuration file
        self.initialization()

    def initialization(self):
        self.RememberedHeroes = 0 # Nb of heroes that society "remembers" in a given round

    def genemap(self):
        """ Defines the name of genes and their position on the DNA.
        """
        return [('SelfSacrifice')] 		# gene length (in bits) is read from configuration

    def display_(self):
        disp = [(i+1,G.name) for (i,G) in enumerate(self.GeneMap)]
        L = len(disp)
        disp += [(L+1, 'RememberedHeroes')]
        return disp
        
    def local_display(self, ToBeDisplayed):
        " allows to diplay locally defined values "
        if ToBeDisplayed == 'RememberedHeroes':
            return self.RememberedHeroes # displaying a quantity that can be computed within the scenario
        return None
        
    def update_positions(self, members, start_location):
        """ locates individuals on an 2D space
        """
        # sorting individuals by gene value
        duplicate = members[:]
        duplicate.sort(key=lambda x: x.gene_value('SelfSacrifice'))
        for m in enumerate(duplicate):
            m[1].location = (start_location + m[0], m[1].Reproductive_points )
            # Allows to place individuals in a 2D field

            ## Other options
            #m[1].location = (start_location + m[0], m[1].Share )
            #m[1].location = (start_location + m[0], m[1].HeroesRelatedness)
            #m[1].location = (start_location + m[0], m[1].gene_value('SelfSacrifice'))
    
    def remove_agent(self, agent):
        " action to be performed when an agent dies "
        # None here, useful for tests
            
########################################
##### Life_game ####
########################################
    def life_game(self, members):
        """ Defines one year of play (outside of reproduction)
            This is where individual's acquire their score
        """
        # First: make initializations (1)
        self.start_game(members)
        # Then: play multipartite game, composed of:
            # The sacrifices game (2):
        AliveMembers = self.sacrifices(members)
            # Social interactions between the living (3)
        for play in range(self.Parameter('Rounds', Default=1)):
            self.interactions(AliveMembers, nb_interactions=self.Parameter('NbInteractions'))
        # Last: work out final tallies (4)
        for indiv in AliveMembers:
            self.evaluation(indiv)
        # "Social" scores are translated into life points, which affect individual's survival (not useful here)
        self.lives(AliveMembers)      


########################################
##### Life_game #### (1) Initializations ####
########################################
    def prepare(self, indiv):
        """ Defines what is to be done at the individual level before interactions
            occur - Used in 'start_game'
        """
        indiv.Reproductive_points = 0   # Reset reproductive points to 0

    def start_game(self, members):
        """ Defines what is to be done at the group level each year
            before interactions occur - Used in 'life_game'
        """
        for indiv in members:	self.prepare(indiv)

########################################
##### Life_game #### (2) Self-sacrifices ####
########################################
            ## (2a) Individual propensity to self-sacrifice
    def deathProbability(self, indiv):
        """ Converts an individual's genetic propensity to self-sacrifice into a probability
            Used in 'selfSacrifice'
        """
        maxvalue = 2 **	self.Parameter('GeneLength') - 1
        return (indiv.gene_value('SelfSacrifice') / maxvalue)

    def selfSacrifice(self, indiv):
        """ An agent decides to make the ultimate sacrifice
            Self-Sacrifice is only a possibiltiy from a certain age (e.g. adulthood)
            and is controlled by the SelfSacrifice gene (see deathProbability)
            Used in 'sacrifices'
        """
        p = self.deathProbability(indiv)
        ## 'Probablistic' mode:
        bool = p > random() 

        # Other (unused) modes:
        ## 'Binary mode': (Individuals are programmed to self-sacrifice at a certain age)
        #bool = p > 0 and (indiv.age > ((percent(self.Parameter('SacrificeMaturity')) * self.Parameter('AgeMax'))))
        ## 'Threshold mode': gene codes for the value of the age after which sacrifice occurs
        # This is a measure of the 'value' of the sacrifice (how much potential reproduction is given up)
        #bool = indiv.age > (1-p) * self.Parameter('AgeMax')

        indiv.SelfSacrifice = bool
        return bool

########################################
            ## (2b) Population-level self-sacrifice game
    def sacrifices(self, members):
        """ Self-sacrifice 'game':
            Heroes may self-sacrifice "for the good of the group"
            In return they are admired - admiration is exogenous here
            Used in 'life_game'
        """
        Heroes = []
        Cowards = members[:]
        for indiv in members:	# Deciding who are the population's heroes
            if indiv.SelfSacrifice:	# indiv is already a hero (useless here: for earlier version)
                Heroes.append(indiv)
                Cowards.remove(indiv)
            elif self.selfSacrifice(indiv):	# indiv is not already a hero but is given an opportunity to be one
                Heroes.append(indiv)
                Cowards.remove(indiv)
        
        if self.Parameter('Baseline')==0:
            ######## baseline = 0: such that RememberedHeroes is approximately 0 for Admiration = 0
            random_heroes = 1 + int ( self.Parameter('PopulationSize') * (self.Parameter('MutationRate') / 1000 ) / self.Parameter('GeneLength'))
            self.RememberedHeroes = self.memo_heroes(len(Heroes)-random_heroes, Cowards, threshold = self.Parameter('RemThreshold'))
                # Substracting heroes that can be accounted for by 'pure chance' (mutation)
        else:
            ####### baseline > 0 version (not used)
            self.RememberedHeroes = self.memo_heroes(len(Heroes), Cowards, threshold = self.Parameter('RemThreshold'))
        
        self.inc_shares(Heroes, Cowards)    # Relatives of heroes gain shares
    
        # Heroes are honored (admired) by society
        Admiration = self.honoring(Cowards, len(Heroes))

        # This spills over to their relatives
        self.spillover(Cowards, Admiration, threshold = self.Parameter('ReproGainsThreshold'))
        
        self.kill_heroes(Heroes)    # Heroes are set to be removed from the simulation
        return Cowards

    def memo_heroes(self, new_heroes, members, threshold = 5):
        " Society, through its (alive)_ individuals, remembers its heroes "
        
        members.sort(key=lambda x: x.HeroesWitnessed, reverse = True)

        past_heroes = members[ int( percent(threshold) * len(members) )].HeroesWitnessed   
        # Heroes pass off to posterity if they are "remembered" by a sufficient amount of alive individuals (threshold %)

        for indiv in members:
            indiv.HeroesWitnessed += new_heroes
        return past_heroes + new_heroes

    def inc_shares(self, heroes, members):
        """ Relatives of heroes indirectly benefit from their sacrifice
        by gaining shares (useful in 'spillover')
        """
        for Hero in heroes:
            for Child in Hero.Children:
                Child.Share += 1

    def honoring(self, worshippers, nb_heroes):
        """ Defines the amount of available population-level admiration for heroes
            (To be overloaded)
        """
        if nb_heroes == 0: return 0 # No heroes to admire this round
        return self.Parameter('Admiration') * len(worshippers)

    def spillover(self, members, admiration = 0, threshold = 10):
        """ Societies' admiration for heroes "spills over" to their relatives 
            who gain reproductive points (Selectivity mode)
        """
        tot_share = 0
        for indiv in members:
            tot_share += indiv.Share
        if tot_share == 0:
            return
        for indiv in members:
            indiv.Reproductive_points += indiv.Share / tot_share * admiration
            indiv.Reproductive_points = int(indiv.Reproductive_points /threshold) # Only points above threshold entail reproductive advantage 

    def kill_heroes(self, heroes):
        " Heroes are programmed to die (see 'lives') "
        for Hero in heroes:
            Hero.LifePoints = -1

########################################
##### Life_game #### (3) Social interactions ####
#######################################
    def interactions(self, members, nb_interactions = 1):
        """	Defines how the (alive) population interacts
            Used in 'life_game'
        """
        for inter in range(nb_interactions):
            if not members: return
            Fan = choice(members)
            # Fan chooses friends from a sample of Partners
            Partners = self.partners(Fan, members, int(percent(self.Parameter('SampleSize')\
                                                                    * (len(members)-1) )))
            self.interact(Fan, Partners)

    def interact(self, indiv, partners):
        """ Nothing by default - Used in 'interactions'
        """
        pass

    def partners(self, indiv, members, sample_size = 1):
        " Decides whom to interact with - Used in 'interactions' "
        #By default, a sample of partners is randomly chosen
        partners = members[:]
        partners.remove(indiv)
        if sample_size > len(partners):
            return partners
        if partners != []:
            return sample(partners, sample_size)
        else:
            return None
    
    def partner(self, indiv, members):
        """ Decides whom to interact with - Used in 'life_game'
        """
        # By default, a partner is randomly chosen
        partners = members[:]
        partners.remove(indiv)
        if partners != []:
            return choice(partners)
        else:
            return None
                    
    def interaction(self, indiv, partner):
        " Nothing by default - Used in 'life_game' "
        pass

########################################
##### Life_game #### (4) Computing scores and life points ####
########################################
    def evaluation(self, indiv):
        " Computation of social score"
        # No social score by default
        pass    # Reproductive points are computed in 'spillover' (see 'sacrifices')

    def lives(self, members):
        """ Converts alive members' scores into life points - used in 'life_game'
        """
        # Selectivity mode: no life points by default
        return


########################################
#### Reproduction ####
########################################
# Reproduction is already defined elsewhere, but some functions have to be overloaded to create local individuals
# This is the case with parenthood (here) and Group.reproduction
    def parenthood(self, RankedCandidates, Def_Nb_Children):
        """ Determines the number of children depending on rank
            Here, Selectivity is non-null by default, leading to rapid (non-linear) convergence
            (contrary to a purely SelectionPressure mode)
        """
        ValidCandidates = RankedCandidates[:]
        for Candidate in RankedCandidates:
            if Candidate.SelfSacrifice or Candidate.age < self.Parameter('AgeAdult'):
                ValidCandidates.remove(Candidate)	# Children and (dead) heroes cannot reproduce (AgeAdult is null by default)
        candidates = [[m,0] for m in ValidCandidates]
        # Parenthood is distributed as a function of the rank
        # It is the responsibility of the caller to rank members appropriately
        # Note: reproduction_rate has to be doubled, as it takes two parents to beget a child
        for ParentID in enumerate(ValidCandidates):
            candidates[ParentID[0]][1] = chances(decrease(ParentID[0],len(ValidCandidates), self.Parameter('Selectivity')), 2 * Def_Nb_Children)
        return candidates


########################################
########################################
########################################
# Adding useful characteristics to individuals

class Individual(EI.EvolifeIndividual):
    "   Defines what an individual consists of "

    def __init__(self, Scenario, ID=None, Newborn=True):
        # Specific characteristics pertaining to this scenario
        self.SelfSacrifice = False  # True if individual decides to self-sacrifice this year
        self.HeroesWitnessed = 0    # Keeps track of heroes that died during individual's life
        self.Reproductive_points = 0    # Determines number of offspring (Selectivity)
        self.Share = 0              # Determines share of population-level admiration that spills over to individual, if any
        self.Children = []          # Keeps track of individual's children

        # General characteristics: individual inherits from the EvolifeIndividual module
        EI.EvolifeIndividual.__init__(self, Scenario, ID=ID, Newborn=Newborn)

    def inherit_share(self, mom, dad, heredity = 0.5):
        " Individual inherits shares from his parents "
        self.Share += (mom.Share + dad.Share ) / 2 * heredity

    def isChild(self, Indiv):
        if Indiv in self.Children: return True
        return False

    def addChild(self, child):
        " Adds child to list "
        self.Children.append(child)

    def removeChild(self, child):
        """ Removes a child of self
            Used when the child dies (see 'Group.remove_')
        """
        if self.isChild(child):
            self.Children.remove(child)
    

########################################
########################################
########################################
# Overloading useful elements of Group module with local Individual class

class Group(EG.EvolifeGroup):
    """ The group is a container for individual (By default the population only has one)
        It is also the level at which reproduction occurs
        Individuals are stored in self.members
    """

    def __init__(self, Scenario, ID=1, Size=100):
        EG.EvolifeGroup.__init__(self, Scenario, ID, Size)

    def createIndividual(self, ID=None, Newborn=True):
        " Calling local class 'Individual'"
        Indiv = Individual(self.Scenario, ID=self.free_ID(), Newborn=Newborn)
        # Individual creation may fail if there is no room left
        self.Scenario.new_agent(Indiv, None)  # Let scenario know that there is a newcomer (unused)
        return Indiv

    def update_ranks(self, flagRanking = False, display=False):
        """ Updates various facts about the group
        """
        # Removing individuals who die of old age (as defined by AgeMax)
        for m in self.members[:]:  # must duplicate the list to avoid looping over a modifying list
            if m.dead():	self.remove_(self.members.index(m))
        self.size = len(self.members)
        if self.size == 0:	return 0
        # ranking individuals
        if flagRanking:
            # ranking individuals in the group according to their score
            self.ranking = self.members[:]	  # duplicates the list, not the elements
            self.ranking.sort(key=lambda x: x.Reproductive_points,reverse=True)
            if self.ranking != [] and self.ranking[0].Reproductive_points == 0:
                # all scores are zero
                shuffle(self.ranking)  # not always the same ones first
            self.best_score = self.ranking[0].score()
        return self.size

    def update_(self, flagRanking = False, display=False):
        """ Updates various facts about the group + positions
        """
        size = Group.update_ranks(self, flagRanking=flagRanking)
        if display:
            if flagRanking:	self.Scenario.update_positions(self.ranking, self.location)
            else:			self.Scenario.update_positions(self.members, self.location)
        # updating social links
        for m in self.members:	m.checkNetwork(membershipFunction=self.isMember)
        return size


    def remove_(self, memberNbr):
        " An individual is removed from the group and his parents' family trees "
        indiv = self.whoIs(memberNbr)
        for parent in self.members:
            parent.removeChild(indiv)
        return EG.EvolifeGroup.remove_(self, memberNbr)

    def reproduction(self):
        """ Reproduction within the group
            Uses 'parenthood' (in Scenario) and 'couples' (not reproduced here - from Group module)
            'couples' returns as many couples as children are to be born
        """
        # The probability of parents to beget children depends on their rank within the group
        # (Except if Selectivity = 0, for which rank becomes random)
        self.update_(flagRanking=True)   # updates individual ranks
        for C in self.Scenario.couples(self.ranking):
            # Making of the child
            child = Individual(self.Scenario,ID=self.free_ID(), Newborn=True)
            if child:
                child.hybrid(C[0],C[1]) # Child's DNA results from parents' DNA crossover
                child.mutate()
                # Child inherits shares: thus grand-children (and so on) also indirectly benefit from self-sacrifice
                child.inherit_share(C[0],C[1], heredity = percent(self.Scenario.Parameter('SacrificeHeredity')))
                child.update()  # Computes the value of genes, as DNA is available only now
                if self.Scenario.new_agent(child, C):  # Let scenario decide something about the newcomer (not used here)
                        # Child is added to parents' children lists
                    C[0].addChild(child)
                    C[1].addChild(child)
            
                    self.receive(child) # Adds child to the group


########################################
########################################
########################################
# Overloading useful elements of Population module with local Group class

class Population(EP.EvolifePopulation):
    """ Defines the population of agents
        This is the level at which 'life_game' is played
    """

    def __init__(self, Scenario, Observer):
        " Creates a population of agents "
        EP.EvolifePopulation.__init__(self, Scenario, Observer)
        self.Scenario = Scenario

    def createGroup(self, ID=0, Size=0):
        " Calling local class 'Group' "
        return Group(self.Scenario, ID=ID, Size=Size)

########################################
########################################
########################################
# Launching of the simulation, using Start module, and which capabilities to use: 
# displays over time (average gene value and remembered heroes here), 2D field, genes, social networks

def Start(Gbl = None, PopClass = Population, ObsClass = None, Capabilities = 'PCGFN'):
    " Launch function "
    if Gbl == None: Gbl = Scenario()
    if ObsClass == None: Observer = EO.EvolifeObserver(Gbl)	# Observer contains statistics
    Pop = PopClass(Gbl, Observer)
    BatchMode = Gbl.Parameter('BatchMode')

    if BatchMode:   # Non-graphic mode (for large-scale experiments)
        EB.Start(Pop.one_year, Observer)
    else:
        EW.Start(Pop.one_year, Observer, Capabilities=Capabilities)
    if not BatchMode:	print("Bye.......")
    sleep(2.1)	
    return



if __name__ == "__main__":
    print(__doc__)

    #############################
    # Global objects			#
    #############################
    Gbl = Scenario()
    Start(Gbl)
