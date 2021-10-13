import requests

# service to make api call
# this could've been in the controller class, but for modularity, it's nice having separate services for interactions with APIs
class tfl_service:

    def get_disruptions(lines):
        lines_string = ""
        for line in lines:
            lines_string = lines_string + line+ ","
        s1 = slice(0, len(lines_string)-1, 1)
        lines_string = lines_string[s1]
        return requests.get('https://api.tfl.gov.uk/Line/'+lines_string+'/Disruption')