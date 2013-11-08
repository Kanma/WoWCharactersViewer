# WoWCharactersViewer

Script that generate a web page containing informations about the World of Warcraft
characters you are interested in.


## Requirements

Download the required submodules by executing:

`$ git submodule init
$ git submodule update`


## Execution

Usage: `./process.py [--data <path>] [<dest_folder>]`

The default value for *dest_folder* is `./html`.

The (optional) *--data* option is used to indicates the folder where the game add-ons
saves their data (for instance, on OS X:
/Applications/World\ of\ Warcraft/WTF/Account/<username>/). The script will look there if
there is some data produced by the AskMrRobot add-on.

It will produce a JSON file (*data.json*) in *dest_folder*.

The *process.py* script needs a file called *settings.py* that contains informations about
the characters you want to display. Here is an example one:

`# List of all the characters to retrieve, format: (region, server, character)
CHARACTER_NAMES = [
    ('eu', 'Khaz Modan', 'SomeCharacter'),
    ('eu', 'Khaz Modan', 'AnotherCharacter'),
]`


`# Valid values: us, eu, kr, tw, cn
LOCALE = 'fr'`


## Display

Copy the content of the *html* folder and the *data.json* file on your web server and
open it in your browser.


## License

WoWCharactersViewer is is made available under the MIT License. The text of the license is
in the file 'LICENSE'.

Under the MIT License you may use WoWCharactersViewer for any purpose you wish, without
warranty, and modify it if you require, subject to one condition:

>   "The above copyright notice and this permission notice shall be included in
>   all copies or substantial portions of the Software."

In practice this means that whenever you distribute your application, whether as binary
or as source code, you must include somewhere in your distribution the text in the file
'LICENSE'. This might be in the printed documentation, as a file on delivered media, or
even on the credits / acknowledgements of the runtime application itself; any of those
would satisfy the requirement.

Even if the license doesn't require it, please consider to contribute your modifications
back to the community.
