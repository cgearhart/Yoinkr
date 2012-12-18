import urllib2
import re
import os
import html5lib

from html5lib import treebuilders, treewalkers

save_dir = os.path.expanduser('~/Downloads')

base_url = 'http://www.flickr.com/photos/christopherandvalerie/sets/72157631605078931/?page=%d'
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_2) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.95 Safari/537.11'}
image_num_re = re.compile(r'.*/(\d+)/in/.*')

pic_url = 'http://www.flickr.com/photos/christopherandvalerie/%s/sizes/o/in/set-72157631605078931/'
re_original_image = re.compile(r'(.+farm9.+/\w+_o.+)')
re_filename = re.compile(r'.+/(\w+_o.+)')


def get_html(url,headers_dict):
    req = urllib2.Request(url)
    for key,header in headers_dict.iteritems():
        req.add_header(key, header)
    response = urllib2.urlopen(req)
    return response.read()


def parse_with_html5lib(html_doc):
    p = html5lib.HTMLParser(tree=treebuilders.getTreeBuilder("dom"))
    dom_tree = p.parse(html_doc)
    walker = treewalkers.getTreeWalker("dom")
    return walker(dom_tree)


def get_hrefs(dom_walker):
    links = []

    for token in dom_walker:
        if token.has_key('data'):
            if token.has_key('name') and token['name'] == u'a':
                data = token['data']
                if data.has_key((None, u'href')):
                    #print data[(None, u'href')]
                    links.append(data[(None, u'href')])
    return links


def get_imgs(dom_walker):
    img = []

    for token in dom_walker:
        if token.has_key('name') and token['name'] == u'img':
            data = token['data']
            if data.has_key((None, u'src')):
                img.append(data[(None, u'src')])
    return img


def filter_elements(elements, reg_exp):
    return [reg_exp.match(element).group(1) for element in elements if reg_exp.match(element)]


def get_elements(url, element_getter):        
    html_response = get_html(url,headers)
    dom_walker = parse_with_html5lib(html_response)
    return element_getter(dom_walker)


def collect_names():
    image_nums = {}

    for this_url in [base_url % n for n in xrange(1,5)]:
        for num in filter_elements(get_elements(this_url,get_hrefs),image_num_re):
            if not image_nums.has_key(num):
                image_nums[num] = None
    return image_nums.keys()


def collect_static_links(pic_list):
    static_image_list = []

    for num in pic_list:
        this_url = pic_url % num
        original_size_image_url = filter_elements(get_elements(this_url,get_imgs), re_original_image)
        static_image_list += original_size_image_url

    return static_image_list

def download_images(static_links):
    idx = len(static_links)
    for url in static_links:
        img = get_html(url,headers)
        fname = re_filename.match(url).group(1)
        with open(os.path.join(save_dir,fname),'wb') as f:
            print '%d: saving %s as %s in %s' % (idx,url,fname,save_dir)
            f.write(img)
            print 'Done.'
        idx -= 1

if __name__=="__main__":

    print 'Collecting the names of all images in the set.'
    image_num_list = collect_names()
    print 'Found %d images in the set.' % len(image_num_list)
    print 'Collecting static links to the original size image files.'
    image_list = collect_static_links(image_num_list)
    print 'Downloading %d images.' % len(image_list)
    download_images(image_list)
