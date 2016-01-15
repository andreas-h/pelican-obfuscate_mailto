# pelican-obfuscate_mailto

This is a plugin to obfuscate `mailto:` links in Pelican output using a
JavaScript technique developed by Hervé Grall, see
http://www.grall.name/posts/1/antiSpam-emailAddressObfuscation.html#sec-1-5 and
http://www.grall.name/posts/1/onlineTools_obfuscation.html#sec-2-4.

`mailto:` links can only be decrypted with JavaScipt enabled.

## Configuration

`obfuscate_mailto` supports the following configuration settings:

- `OBFUSCATE_MAILTO_REPLACE_TEXTCONTENT`: A boolean value; if `True`, the
  `.textContent` of each `<a>` element will be replaced with the decrypted mail
  address. Defaults to `False`.
