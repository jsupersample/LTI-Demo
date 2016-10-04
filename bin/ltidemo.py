import json
import web
import ssl
import os
from web.wsgiserver import CherryPyWSGIServer
from urllib import urlopen
import urllib

#set up path to the html template and map it to the root address
urls = (
  '/', 'index'
)

#Url to your canvas installation and private key
base_url = os.environ['BASE_URL']
token=os.environ['API_KEY']

#set up web.py environment and point to html template
app = web.application(urls, globals())
render = web.template.render('templates/')


class index: #handle call to index defined above
    def POST(self): #handle the HTTP POST verb

    	post_data = web.input() #load variables passed from URL and LTI click
	
	    #If there is a next variable passed from the url, grab its value.
	    #Otherwise set a default. This is used later to indicate if the next button 
	    #was clicked and where to go if it was
        try:
            next = post_data.next 
        except Exception as e:
            next = "default"
        
        #Same thing for the prev variable.
        try:
            prev = post_data.prev
        except Exception:
            prev = "default"

        #logic to figure out which student to load.
        if (next=="default") and (prev=="default"): #this condition means it's the first click. We load the first student.
            enrollments_url = base_url+"courses/"+post_data.custom_canvas_course_id+"/enrollments?per_page=1&type=StudentEnrollment&access_token="+token
        elif prev!="default": #This means the previous button was clicked. We load the previous student
            enrollments_url = urllib.unquote_plus(prev)+"&access_token="+token
        else: #This means that "next" is set, so that was clicked. We load that student.
            enrollments_url = urllib.unquote_plus(next)+"&access_token="+token

        u = urlopen(enrollments_url) #call the Canvas RESTful API.

        enrollment = json.loads(u.read())[0] #parse the json object returned by the API

        user_id = str(enrollment["user_id"]) #from the json, get the user's numeric id.
        profile_url = "users/"+user_id+"/profile?access_token="+token #build the url to their profile (another API call).
        profile_request = urlopen(base_url+profile_url) #grab the profiel from the API.
        profile = json.loads(profile_request.read()) #parse the json returned.

        #This section handles the "Link" headers returned by the 
        links = parse_link(u.headers['Link']) #details below
        try: #try to read the "next" link. 
            next_link = links["rel=next"]
        except Exception: #set a default if it isn't. This means we are on the last page.
            next_link = "default"

        try: #Same as above, but for the previous page.e
            prev_link = links["rel=prev"]
        except Exception:
            prev_link = "default"

        #The links above will be passed in the URL, so special characters need to be encoded.
        next_link_encoded = "/?next="+urllib.quote_plus(next_link)
        prev_link_encoded = "/?prev="+urllib.quote_plus(prev_link)

        #finish this script and send these variables to the template.
        return render.index(profile = profile, next=next_link_encoded, prev = prev_link_encoded)



#utility to parse the next and previous Link headers.
def parse_link(text):
	links = {} #create an empty dictionary.
	headers = text.split(',') #divide the links.
	for link in headers: #iterate through each link.
		parts = link.split(';') #break apart on the semi-colon
		#use the second part for the key and the first for the value.
		links[parts[1].strip().replace("\"","")] = parts[0].strip().replace("<","").replace(">","")
	return links #return the dictionary.


if __name__ == "__main__":
    app.run()
