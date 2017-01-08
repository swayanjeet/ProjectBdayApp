import facebook
import requests

ACCESS_TOKEN = "EAAX7retDkCcBAPWQ3Xpcl9jnu1ptbueYYeDmN1AnBIupGTBXhvI1XFDxujphJgvTFSB64Fdo6GtDRuRdVvKNyEYlgOorTuw17Me6129hKj9iBGNRRGxW4rHeZADi2ZCyauHwCTKOkazXRyprJDvD5PvW5tjrUuwltUz6XAVAZDZD"
graph = facebook.GraphAPI(ACCESS_TOKEN)
friends = graph.get_connections("me","friends")

allfriends = []

# Wrap this block in a while loop so we can keep paginating requests until
# finished.
while(True):
    try:
        for friend in friends['data']:
            allfriends.append(friend['id'].encode('utf-8'))
        # Attempt to make a request to the next page of data, if it exists.
        friends=graph.get_connections("me","friends",after=friends['paging']['cursors']['after'])
    except KeyError:
        # When there are no more pages (['paging']['next']), break from the
        # loop and end the script.
        break
print allfriends