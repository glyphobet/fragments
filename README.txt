Differencing Fragmentation Manager
==================================

Operations:

Operations starting from working tree:

 • Add new root
 • Add new file and detect common sequences and generate parent node with those sequences
 • Modify a leaf and apply modifications in that leaf to all leaves with that sequence (cherry-picking)
 • Modify a leaf and don't apply modifications and generate a new leaf accordingly

Operations starting from repository:

 • Modify a sequence (commit a changeset up the tree and rebase)
 • Sprout a new leaf (branch)

