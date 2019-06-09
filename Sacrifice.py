##############################################################
# EVOLIFE              http://evolife.telecom-paristech.fr   #
# Telecom ParisTech  2018               Jean-Louis Dessalles #
# ---------------------------------------------------------- #
# License:  Creative Commons BY-NC-SA                        #
##############################################################


""" Study of the possibility of self-sacrifice being an ESS,
    as first-order signal for patriotism.
    Uses 'Exogenous.py' as Base (overloading useful functions)
"""

from math import log
from random import randint, random, choice

import Exogenous as Base

import sys
sys.path.append('..')
sys.path.append('../../..')

import Evolife.Ecology.Alliances as EA
from Evolife.Tools.Tools import percent


class Scenario(Base.Scenario):

########################################
#### General initializations and visual display ####
########################################

    def genemap(self):
        """ Defines the name of genes and their position on the DNA.
        """
        return [('Patriot'), ('NonPatriot'), ('Demand'), ('SelfSacrifice')] 		# gene length (in bits) is read from configuration

    def update_positions(self, members, start_location):
        """ Locates individuals on an 2D space
        """
        duplicate = members[:]
        # sorting individuals by patriotism
        duplicate.sort(key = lambda x: x.Patriotism)
        for m in enumerate(duplicate):
            m[1].location = (start_location + m[0], m[1].SignalLevel)

########################################
##### Life_game #### (1) Initializations ####
########################################
    def prepare(self, indiv):
        """ Defines what is to be done at the individual level before interactions
            occur - Used in 'start_game'
        """
        indiv.score(100, True)  # Sets initial ("social") score to 100
        
        indiv.SignalLevel = 0   # Resets signal level - useful for a non-genetic learning (future ?) version, not here
        indiv.Reproduction_points = 0   # # Reset reproductive points to 0

        # friendship links (lessening with time) are updated (Erosion is null by default)
        indiv.lessening_friendship((100 - self.Parameter('Erosion'))/100.0)

########################################
##### Life_game #### (2) Self-sacrifices ####
########################################

    def honoring(self, worshippers, nb_heroes):
        """ Total social admiration (for heroes)
            depends on the behaviors of all individuals in the 'honoring' game
            (second-order signal)
        """        
        if nb_heroes == 0: return 0 # No heroes to honor
        Offerings = 0
        for Indiv in worshippers:
            if Indiv.Patriotism == 0:   # Indiv is not a patriot
                offering = Indiv.gene_relative_value('NonPatriot')
                if self.Parameter('DifferentialCosts') == 0: # MaxOffer version
                    Indiv.score(- self.costHonor(offering))
                    offering = min(self.Parameter('MaxOffer'), offering)
                        # Non-patriot's offering is capped: 
                        # they already have other investments (in the rival group, in themselves...)
                        # If social demand is too high, this could push them 
                        # (perhaps similar to 'exclusive' signals: one can't wear clothes tied to two social classes at once,
                        # or bear tatoos from two rival gangs...)
                else:   # DiffCosts version
                    Indiv.score( - self.costHonor(offering, DifferentialCosts = True))
                        # Honoring is more costly for non-patriots: investing time (for instance)
                        # in the group is less-interesting than for patriots, since they aren't as committed
                        # to the group and thus stand to gain less in relative terms purely in relation to the group
                        # (opportunity cost)
            else:
                offering = Indiv.gene_relative_value('Patriot')
                Indiv.score (-self.costHonor(offering))

            Indiv.SignalLevel += int( offering / self.Parameter('VisibleThreshold')) * self.Parameter('VisibleThreshold')
            # Signal must surpass a threshold to be visible

            # Visible signals become part of social admiration
            # (In this linear version, number of heroes or distance between members is not a factor)
            Offerings += Indiv.SignalLevel
        return Offerings
    
      
    def costHonor(self, offering, DifferentialCosts = False, patriotism = 0):
        basic_cost = offering * percent(self.Parameter('HonoringCost'))
        if not DifferentialCosts:   # MaxOffer mode: non-patriots face the same cost as patriots
            return basic_cost
        else:   # DiffCosts mode: NonPatriots face a premium for honoring
            return basic_cost + basic_cost * (1 - patriotism) * percent(self.Parameter('DishonestPremium'))

########################################
##### Life_game #### (3) Social interactions ####
########################################
    
    def interact(self, receiver, Signalers):
        """ Receiver selects the first Signaler it sees that matches its demands
            (and that accepts it as a follower)
        """
        Candidates = self.filter(Signalers, receiver.gene_relative_value('Demand'))
        if Candidates == []: return
        for Signaler in Candidates:
            if Signaler.followers.accepts(0) >=0:
                receiver.F_follow(0, Signaler, 0)   
                break   # Signaler and receiver have accepted each other as friends

    def filter(self, Signalers, requirement):
        " Filters out signalers that don't meet the individual's requirements in terms of visible patriotism "
        AcceptableFriends = Signalers[:]
        for Signaler in Signalers:
            if Signaler.SignalLevel < requirement:
                AcceptableFriends.remove(Signaler)
        return AcceptableFriends

    def interact_old(self, indiv, Signalers):
        """ Formation of friendship bonds
            By honoring heroes (see 'honoring'), individuals signal their patriotism
            This signal is used by others to choose their friends
            (keeping in mind this is crucial: see 'evaluation')
        """
        if Signalers == []:	return
        # The agent chooses the first Signaler it sees that matches its demands
        #Signalers.sort(key=lambda S: S.SignalLevel, reverse=True)  # Signalers are not sorted by default
        demand = indiv.gene_relative_value('Demand')
        offer = indiv.SignalLevel  
        for Signaler in Signalers:
            if Signaler == indiv: continue
            if indiv.follows(Signaler): continue
            if demand > Signaler.SignalLevel:
                continue   # No available interesting Signalers
            if offer < Signaler.gene_relative_value('Demand'):
                continue
            if indiv.get_friend(1, Signaler, 1):
                return   # Indiv and Signaler have become friends !
       

########################################
##### Life_game #### (4) Computing scores and life points ####
########################################
    
    def evaluation(self, indiv):
        
        indiv.score( + self.Parameter('JoiningBonus') * indiv.nbFollowers() )

        if indiv.Patriotism ==0 and random() < percent(self.Parameter('NbTraitors')):
            # indiv is a traitor who betrays its friends
            for follower in indiv.followers:
                follower.score(- self.Parameter('DenunciationCost'))    # The betrayed pay a cost
                indiv.score(+ self.Parameter('Judas'))              # Betrayer obtains payment for betrayal
        else:
            for follower in indiv.followers:
                follower.score(+ self.Parameter('FriendshipValue'))
        return

    def lives(self, members):
        """ Converts alive members' scores into life points - used in 'life_game'
        """
        if self.Parameter('EraseNetwork'): self.reinitialize_network(members)   # Reinitialize friendships (0 by default)
        #AliveMembers = self.betrayal(members, Spare=self.Parameter('DenunciationCost')) # unused (see under)
        AliveMembers = members
        if self.Parameter('SelectionPressure') == 0:
            return
        if not AliveMembers:
            return
        BestScore = max([i.score() for i in AliveMembers])
        MinScore = min([i.score() for i in AliveMembers])
        if BestScore == MinScore:
            return
        for indiv in members:
            indiv.LifePoints =  int ( (indiv.score()-MinScore) * self.Parameter('SelectionPressure') / (BestScore - MinScore) )
            # individuals optain between 0 and SP points, depending on score relative to the population

    def betrayal(self, members, Spare=True):
        " Unused: for version where being betrayed leads to death "
        if Spare: return members
        AliveMembers = members[:]
        for i in members:
            if i.Executed:
                AliveMembers.remove(i)
                i.LifePoints = -1
        return AliveMembers

    def reinitialize_network(self, members):
        for i in members:
            i.forgetAll()


########################################
########################################
########################################
# Adding patriotism

class Patriotic_Individual(Base.Individual, EA.Follower):
    "   Individuals now also have a patriotism phenotype "

    def __init__(self, Scenario, ID, maxPatriotism = 100, Newborn=True):
        self.Patriotism = randint(0, 1)     # Binary patriotism

        # Individual inherits from Exogenous
        Base.Individual.__init__(self, Scenario, ID=ID, Newborn=Newborn)

        self.SignalLevel = 0
        self.Executed = False   # Unused (see betrayal)

        # Individual inherits from Follower module (which manages social relations)
        EA.Follower.__init__(self, self.Scenario.Parameter('MaxFriends'), Scenario.Parameter('MaxFriends'))


########################################
########################################
########################################
# Overloading useful elements of Group module with local Patriotic_Individual class

class Group(Base.Group):
    " In each group, patriotism ranges from 0 to group size (simplification) "

    def __init__(self, Scenario, ID=1, Size=100):
        Base.Group.__init__(self, Scenario, ID, Size)

    def createIndividual(self, ID=None, Newborn=True):
        # calling local class 'Individual'
        Indiv = Patriotic_Individual(self.Scenario, ID=self.free_ID(), Newborn=Newborn)
        # Individual creation may fail if there is no room left
        self.Scenario.new_agent(Indiv, None)  # let scenario know that there is a newcomer (unused)
        #if Indiv.location == None:	return None
        return Indiv

    def reproduction(self):
        """ Reproduction within the group (see Exogene) for details
            Calls local class 'Patriotic_Individual'
        """
        self.update_(flagRanking=True)   # updates individual ranks
        for C in self.Scenario.couples(self.ranking):
            # Making of the child
            child = Patriotic_Individual(self.Scenario,ID=self.free_ID(), Newborn=True)
            if child:
                child.hybrid(C[0],C[1]) # Child's DNA results from parents' DNA crossover
                child.mutate()
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

class Patriotic_Population(Base.Population):
    """ Defines the population of agents
    """

    def __init__(self, Scenario, Observer):
        " Creates a population of agents "
        Base.Population.__init__(self, Scenario, Observer)
        self.Scenario = Scenario

    def createGroup(self, ID=0, Size=0):
        " Calling local class 'Group' "
        return Group(self.Scenario, ID=ID, Size=Size)




if __name__ == "__main__":
    print(__doc__)

    #############################
    # Global objects			#
    #############################
    Gbl = Scenario()
    Base.Start(Gbl, Patriotic_Population)