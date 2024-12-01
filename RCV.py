import pandas as pd
import numpy as np
import argparse

def RCV(filename: pd.DataFrame, choiceOrder: list[str]=None, discardPrefix: str="No Confidence", verbose=True):
    '''
    Code for ranked choice voting. Google Forms structure taken from https://www.rcv123.org/google-forms-ranked-choice-spreadsheet-calculator. 
    Least viable candidates determined by least number of top votes with tie handling through extending the logic for successive rankings among current candidates.
    If the least viable candidates are tied in counts on all rankings, one candidate is chosen for removal on random.
    
    ## Params:
        filename -- .csv filepath
        choiceOrder -- order of possible values, optional, default ["1st Choice", "2nd Choice", ..., "30th Choice"]
        discardPrefix -- prefix string to not rank candidate, optional, default "No Confidence"
        verbose -- prints/displays step-by-step calculation and elimination information, optional, default True
    '''
    # load in default params
    choiceOrder = choiceOrder if choiceOrder else ["1st Choice", "2nd Choice", "3rd Choice"] + [f'{i}th Choice' for i in range(4, 31)]
    
    def logDisplay(foo):
        '''
        Helper function to displays() on Jupyter, print() in console when verbose is True
        '''
        if not verbose: return
        try:
            display(foo)
        except:
            print(foo)
            
    def log(foo):
        '''
        Helper function to only print if verbose is True
        '''
        if not verbose: return
        print(foo)
    
    # dict used to map options to numerical ranking ('1st Choice')
    choiceMap = {c: i + 1 for i, c in enumerate(choiceOrder)}
    
    df = pd.read_csv(filename)
    
    df.drop('Timestamp', axis=1, inplace=True)
    df.rename(columns=lambda x: x.split('[')[1][:-1], inplace=True)
    df.index.name = 'voter'
    
    def choiceToInt(choice, choiceMap, discardPrefix):
        if pd.isna(choice) or choice.startswith(discardPrefix):
            return -1

        return choiceMap[choice]

    df = df.applymap(lambda x: choiceToInt(x, choiceMap, discardPrefix))
    
    order = []
    
    def find_least_viable(df):
        '''
        Helper function to hanlde tiebreakers in the least viable candidate elimination through extending the logic to account for successive rankings until the tie is resolved, 
        randomly selecting candidates if ranking is tied all the way.
        '''
        remaining_counts = {candidate: -1 for candidate in df.columns}

        for rank in range(df.shape[1]):
            
            for candidate in remaining_counts.keys():
                remaining_counts[candidate] = (df == rank + 1)[candidate].sum()
            
            # Check for the candidate(s) with the least votes at this rank
            min_votes = min(remaining_counts.values(), key=lambda x: x)
            tied_candidates = {k: v for k, v in remaining_counts.items() if v == min_votes}


            # Otherwise, continue to the next rank
            remaining_counts = tied_candidates
            
            log(f'Least Viable Choice(s) {rank + 1}: {list(tied_candidates.values())[0]} votes - {list(tied_candidates.keys())}')
            
            # If tie is resolved
            if len(remaining_counts) == 1:
                return list(remaining_counts.keys())[0]

        # If still tied after all ranks, choose randomly
        random_least = np.random.choice(list(remaining_counts.keys()))
        log(f'Random Least Viable Choice: {random_least}')
        return random_least
    
    round = 0
    # redistribute vote logic
    while True:
        log(f"=============================== Round {round} ===============================\n")
        logDisplay(df)
        # Count first-choice votes for each candidate
        vote_counts = (df == 1).sum()
        log(f"\nTop Vote Counts:\n{vote_counts}\n")
        
        # If only one candidate remains, stop
        if len(vote_counts) == 1:
            log(f"Winner: {vote_counts.idxmax()}")
            
            order.append(vote_counts.idxmax())
            break
        
        # Identify the least viable candidate
        least_viable = find_least_viable(df) # vote_counts.idxmin()
        log(f"Eliminating: {least_viable}")
        
        log(f"\nRedistributing Votes: ")
        logDisplay(rd_votes := df.loc[df[least_viable] == 1])
        log(f"\nTop Choice Movement (+):")
        logDisplay((rd_votes.loc[:, rd_votes.columns != least_viable] == 2).sum())
        
        # Redistribute votes
        for i, row in df.iterrows():
            if row[least_viable] == 1:  # If this ballot ranked the eliminated candidate first
                for candidate in row.index:
                    if row[candidate] > 1 and candidate != least_viable:
                        df.loc[i, candidate] -= 1  # Promote this candidate
        
        # Remove the eliminated candidate
        df.drop(columns=least_viable, inplace=True)
        order.append(least_viable)
        
        round += 1
        
        log("\n\n\n\n")
    
    # reverses to order of last remaining
    order.reverse() 
    log('\n===\n')
    print(f"Final Ranks:")
    for i, c in enumerate(order):
        print(f'{i + 1}. {c}')
    return order

if __name__ ==  '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('filepath', type=str)
    parser.add_argument('-c', '--choice-order', type=str, default="1st Choice, 2nd Choice, 3rd Choice, 4th Choice")
    parser.add_argument('-d', '--discard-prefix', default="No Confidence")
    parser.add_argument('-v', '--verbose', default=True)
    args = parser.parse_args()
    
    RCV(args.filepath, choiceOrder=args.choice_order.split(', '), discardPrefix=args.discard_prefix)