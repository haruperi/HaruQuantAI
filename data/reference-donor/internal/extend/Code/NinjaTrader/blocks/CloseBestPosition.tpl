<#-- CloseBestPosition -> with NT's ONE aggregated position the best and worst position are the
     same one, so this degenerates to "exit the position (direction-filtered)" - correct exactly
     when one position exists (the SQX default #AllowDuplicateTrades# = false). -->
sqCloseBestOrWorstPosition(<@printParam block "#Direction#" />);
