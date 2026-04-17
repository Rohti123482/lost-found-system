from geopy.distance import geodesic

def calculate_match_score(lost, found):

    score = 0

    # type match
    if lost["entity_type"] == found["entity_type"]:
        score += 2

    # color match
    if lost["color"] == found["color"]:
        score += 2

    # location distance
    lost_location = (lost["latitude"], lost["longitude"])
    found_location = (found["latitude"], found["longitude"])

    distance = geodesic(lost_location, found_location).km

    if distance < 5:
        score += 3

    # description similarity
    if lost["description"] and found["description"]:

        lost_words = set(lost["description"].lower().split())
        found_words = set(found["description"].lower().split())

        common_words = lost_words.intersection(found_words)

        score += len(common_words)

    return score, distance