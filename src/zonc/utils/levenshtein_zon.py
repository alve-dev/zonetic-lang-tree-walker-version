def get_distance(s1, s2):
    # Si una es mucho más larga que otra, ni lo intentamos
    if abs(len(s1) - len(s2)) > 2: 
        return 10 
    
    # Creamos una matriz simple (puro minimalismo)
    if len(s1) < len(s2):
        return get_distance(s2, s1)

    if not s2:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    
    return previous_row[-1]

def suggest_command(user_input, valid_commands, min_dist = 8):
    best_match = None

    for cmd in valid_commands:
        dist = get_distance(user_input, cmd)
        if dist < min_dist:
            min_dist = dist
            best_match = cmd
    return best_match