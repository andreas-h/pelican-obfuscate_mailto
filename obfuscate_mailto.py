# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
import random
# import re
import string

from pelican import contents, generators, signals

from bs4 import BeautifulSoup

import logging
log = logging.getLogger(__name__)


# # regex from https://gist.github.com/dideler/5219706
# _pattern = ("([a-z0-9!#$%&'*+\/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+\/=?^_`"
#             "{|}~-]+)*(@|\sat\s)(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?(\.|"
#             "\sdot\s))+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)")
# _regex = re.compile(_pattern)


def encrypt_mail(address, origin, size, key):
    # This function is based on JavaScript code by Hervé Grall, see
    # www.grall.name/posts/1/onlineTools_obfuscation.html#sec-2-4
    s, e, pos = 0, '', 0
    for c in key:
        s += ord(c)
    shift = s % len(address)
    for i in range(len(address)):
        j = (i + shift) % len(address)
        e += chr((ord(address[j]) - origin + ord(key[pos]) - origin) %
                 size + origin)
        pos = (pos + 1) % len(key)
    return e


def decrypt_function(origin, size, key, do_replace_link_textcontent=False):
    # JavaScript functions by Hervé Grall, see
    # www.grall.name/posts/1/antiSpam-emailAddressObfuscation.html#sec-1-5
    # and www.grall.name/posts/1/onlineTools_obfuscation.html#sec-2-4
    if do_replace_link_textcontent:
        replace_textcontent = '      element.textContent=decrypt(y).substring(7);'
    else:
        replace_textcontent = ''
    body = '''<script language="JavaScript" type="text/javascript">
  function openMailer(element) {{
      var y = element.getAttribute("gaia");
      element.setAttribute("href", decrypt(y));
      element.setAttribute("onclick", "");{replace_textcontent}
      delete element.gaia;
    }};
  
  function decrypt(word) {{
    var key = "{key}"
    var s = 0
    for (var i = 0; i < key.length; i++) {{
      s = s + key.charCodeAt(i)
    }}
    var pos = 0
    var first = s % word.length
    var prefix = ''
    var suffix = ''
    for (var i = 0; i < word.length - first; i++) {{
      suffix = suffix + String.fromCharCode((word.charCodeAt(i) + {size} - key.charCodeAt(pos)) % {size} + {origin})
      pos = (pos + 1) % key.length
    }}
    for (var i = word.length - first; i < word.length; i++) {{
      prefix = prefix + String.fromCharCode((word.charCodeAt(i) + {size} - key.charCodeAt(pos)) % {size} + {origin})
      pos = (pos + 1) % key.length
    }}
    var d = prefix + suffix
    return d;
  }}
</script>'''.format(origin=origin, size=size, key=key,
                    replace_textcontent=replace_textcontent)
    return body


def process_html(content, generator):
    if isinstance(content, contents.Static):
        return

    # random parts of obfuscation algorithm
    random.seed(os.path.split(content.source_path)[1])
    origsizepart, keysize = random.randint(10, 117),  random.randint(8, 20)
    origin, size = origsizepart, 127 - origsizepart
    chars = string.ascii_lowercase
    key = ''.join(random.choice(chars) for _ in range(keysize))

    insert_decrypt = False

    # html = re.sub(_regex, obfuscate_mail, content._content)
    html = content._content

    soup = BeautifulSoup(html, 'html.parser')

    for link in soup.findAll('a'):
        href = None
        for k in link.attrs:
            if k.lower() == 'href':
                href = k
        if href:
            if not link.attrs[href].startswith('mailto:'):
                continue
            log.debug('Obfuscating {0} in {1}'.format(link.attrs[href],
                                                      content.source_path))
            mailto = link.attrs[href]
            link.attrs[href] = 'click:address.will.be.decrypted.by.javascript'
            link.attrs['onclick'] = 'openMailer(this);'
            link.attrs['gaia'] = encrypt_mail(mailto, origin, size, key)
            insert_decrypt = True

    soup.renderContents()
    content._content = soup.decode()

    # insert JavaScript functions into <body/>
    if insert_decrypt:
        r_ = generator.settings.get('OBFUSCATE_MAILTO_REPLACE_TEXTCONTENT')
        content._content += decrypt_function(origin, size, key, r_)


def process_all_html(content_generators):
    for generator in content_generators:
        if isinstance(generator, generators.ArticlesGenerator):
            for article in generator.articles + generator.translations:
                process_html(article, generator)
        elif isinstance(generator, generators.PagesGenerator):
            for page in generator.pages:
                process_html(page, generator)


def register():
    signals.all_generators_finalized.connect(process_all_html)
