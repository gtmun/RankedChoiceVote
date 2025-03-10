import streamlit as st
import pandas as pd
import numpy as np

# Helper function to display or print information
def logDisplay(foo, verbose):
    if verbose:
        st.write(foo)

def log(foo, verbose):
    if verbose:
        st.write(foo)

# Function to map choices to numerical rankings
def choiceToInt(choice, choiceMap, discardPrefix):
    if pd.isna(choice) or choice.startswith(discardPrefix):
        return -1
    return choiceMap[choice]

# Main RCV function adapted for Streamlit
def RCV(df, choiceOrder, discardPrefix, verbose):
    # Map choices to numerical rankings
    choiceMap = {c: i + 1 for i, c in enumerate(choiceOrder)}
    
    # Convert choices to numerical rankings
    df = df.applymap(lambda x: choiceToInt(x, choiceMap, discardPrefix))
    
    order = []
    round = 0
    
    while True:
        log(f"=============================== Round {round} ===============================", verbose)
        
        # Display current state of the dataframe
        logDisplay(df, verbose)
        
        # Count first-choice votes for each candidate
        vote_counts = (df == 1).sum()
        
        log(f"\nTop Vote Counts:\n{vote_counts}", verbose)
        
        # If only one candidate remains, stop
        if len(vote_counts) == 1:
            log(f"Winner: {vote_counts.idxmax()}", verbose)
            order.append(vote_counts.idxmax())
            break
        
        # Identify the least viable candidate
        def find_least_viable(df):
            remaining_counts = {candidate: -1 for candidate in df.columns}
            
            for rank in range(df.shape[1]):
                for candidate in remaining_counts.keys():
                    remaining_counts[candidate] = (df == rank + 1)[candidate].sum()
                
                min_votes = min(remaining_counts.values(), key=lambda x: x if x != -1 else float('inf'))
                tied_candidates = {k: v for k, v in remaining_counts.items() if v == min_votes and v != -1}
                
                log(f'Least Viable Choice(s) {rank + 1}: {list(tied_candidates.values())[0]} votes - {list(tied_candidates.keys())}', verbose)
                
                # If tie is resolved
                if len(tied_candidates) == 1:
                    return list(tied_candidates.keys())[0]
                
                # If still tied after all ranks, choose randomly
                remaining_counts = tied_candidates
            
            random_least = np.random.choice(list(remaining_counts.keys()))
            log(f'Random Least Viable Choice: {random_least}', verbose)
            return random_least
        
        least_viable = find_least_viable(df)
        
        log(f"Eliminating: {least_viable}", verbose)
        
        log(f"\nRedistributing Votes: ", verbose)
        
        # Display votes to redistribute
        rd_votes = df.loc[df[least_viable] == 1]
        logDisplay(rd_votes, verbose)
        
        log(f"\nTop Choice Movement (+):", verbose)
        
        # Display top choice movement
        logDisplay((rd_votes.loc[:, rd_votes.columns != least_viable] == 2).sum(), verbose)
        
        # Redistribute votes
        for i, row in df.iterrows():
            if row[least_viable] == 1: # If this ballot ranked the eliminated candidate first
                for candidate in row.index:
                    if row[candidate] > 1 and candidate != least_viable:
                        df.loc[i, candidate] -= 1 # Promote this candidate
        
        # Remove the eliminated candidate
        df.drop(columns=least_viable, inplace=True)
        
        order.append(least_viable)
        
        round += 1
        
        log("\n\n\n\n", verbose)
    
    # Reverse order to show final ranks
    order.reverse()
    
    log('\n===\n', verbose)
    
    st.write(f"Final Ranks:")
    for i, c in enumerate(order):
        st.write(f'{i + 1}. {c}')

# Streamlit App
def main():
    st.title("Ranked Choice Voting App")
    
    # File upload
    uploaded_file = st.file_uploader("Choose a CSV file", type='csv')
    
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        
        # Remove Timestamp column if present
        if 'Timestamp' in df.columns:
            df.drop('Timestamp', axis=1, inplace=True)
        
        # Rename columns if they have brackets
        df.columns = [col.split('[')[1][:-1] for col in df.columns]
        
        # Input parameters
        choiceOrder = st.text_input("Enter choice order (comma-separated, e.g., 1st Choice, 2nd Choice)", 
                                    value="1st Choice, 2nd Choice, 3rd Choice")
        choiceOrder = [c.strip() for c in choiceOrder.split(',')]
        
        discardPrefix = st.text_input("Enter discard prefix (default: No Confidence)", 
                                      value="No Confidence")
        
        verbose = st.checkbox("Show detailed elimination steps", value=True)
        
        # Run RCV
        if st.button("Run Ranked Choice Voting"):
            RCV(df, choiceOrder, discardPrefix, verbose)

if __name__ == "__main__":
    main()