import urllib2
import re
import os
import html5lib

from html5lib import treebuilders, treewalkers


save_dir = os.path.expanduser('~/Downloads')
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_2) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.95 Safari/537.11'}

set_url = 'http://www.flickr.com/photos/christopherandvalerie/sets/72157631605078931/?page=%d'
image_set_urls = [set_url % idx for idx in xrange(1,5)]
pic_url = 'http://www.flickr.com/photos/christopherandvalerie/%s/sizes/o/in/set-72157631605078931/'

image_num_re = re.compile(r'.*/(\d+)/in/.*') #cuts the image id number from the url
original_size_url_re = re.compile(r'(.+farm9.+/\w+_o.+)') #finds links that start with "farm9"
re_filename = re.compile(r'.+/(\w+_o.+)') #returns the filename portion of the URL


def get_resource(url,headers_dict):
    """open a url and return the contents as a file like object."""
    req = urllib2.Request(url)
    for key,header in headers_dict.iteritems():
        req.add_header(key, header)
    response = urllib2.urlopen(req)
    return response.read()


def html5lib_walker(html_doc):
    """given an HTML document, parse it & return a walker object representation"""
    p = html5lib.HTMLParser(tree=treebuilders.getTreeBuilder("dom"))
    dom_tree = p.parse(html_doc)
    walker = treewalkers.getTreeWalker("dom")
    return walker(dom_tree)


def parse_urls(url_list, headers_dict, tag_filter):
    name_list = {}

    for this_url in url_list:
        html_response = get_resource(this_url,headers_dict)
        dom_walker = html5lib_walker(html_response)
        for element in tag_filter(dom_walker):
            name_list[element] = None  #add id_num to the dictionary as a key (enforces uniqueness)

    return name_list.keys()


def get_tags(dom_walker,name,key):
    tags = []

    for token in dom_walker:
        if token.has_key('name') and token['name'] == name:
            data = token['data']
            if data.has_key((None, key)):
                tags.append(data[(None, key)])
    return tags


def only_hrefs_filter(dom_walker):
    return get_tags(dom_walker,u'a',u'href')


def only_imgs_filter(dom_walker):
    return get_tags(dom_walker,u'img',u'src')


def download_images(url_list):
    while url_list:
        url = url_list.pop()
        img = get_resource(url,headers)
        fname = re_filename.match(url).group(1)
        with open(os.path.join(save_dir,fname),'wb') as f:
            print '%d: saving %s as %s in %s' % (len(url_list)+1,url,fname,save_dir)
            f.write(img)
            print 'Done.'

def collect_data(url_list,headers_dict,tag_filter,re_filter):
    tags = parse_urls(url_list,headers_dict,tag_filter)
    return [re_filter.match(tag).group(1) for tag in tags if re_filter.match(tag)]


if __name__=="__main__":

    print 'Collecting the names of all images in the set.'
    image_ids = collect_data(image_set_urls, headers, only_hrefs_filter, image_num_re)

    image_pages = [pic_url % im_id for im_id in image_ids] #substitute each id number into the picture url template

    print 'Found %d images in the set.' % len(image_pages)
    print 'Collecting links to the original size version of each image.'
    original_size_urls = collect_data(image_pages, headers, only_imgs_filter, original_size_url_re)
    
    print 'Downloading %d images.' % len(original_size_urls)
    download_images(original_size_urls)
