#!/bin/bash
#
# voter-raffle.sh
#
# Select a random voter as the winner of the raffle.

# Excludde users:
#    unfa         First place
#    J.Ruegg      Second place
#    lilith93     Third place
#    kay'         by request

flask compo raffle -e "unfa,J.Ruegg,lilith93,kay" | tee winner.txt
