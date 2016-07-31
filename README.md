# biblint
biblint is a small Python utility to plausibilize and check LaTeX and BibTeX
bibliography files for integrity. Since linting of TeX files was functionality
that was added later on, the name is a tiny bit misleading. But it would be
even more confusing to rename it, since there's already packages called
"textlint", which would sound very similar to "texlint". Hence, biblint. It
does not contain a true BibTeX parser, but relies on some crude assumptions
regarding the layout of the BibTeX file:

- Beginning of entries start with @foo{bar, in a single line
- Any line that looks like "identifier = .\*" is treated as a new key within an
  entry
- End of entry must have } at beginning of the line

Cross-references are not supported.



### License
biblint is licensed under the GNU General Public License version 3. A copy of
the license should be included in the package in the LICENSE file.



### Author
biblint was written by Johannes Bauer. The project is hosted on GitHub at
https://github.com/johndoe31415/biblint. For further information, visit
http://johannes-bauer.com.



### Requirements
To run biblint, Python 3 is required. The mako templating engine is used for
HTML export and is required currently (even if you do not plan to do HTML
exports). For fuzzy matching of titles, the fuzzywuzzy package is required. If
you do not have fuzzywuzzy installed, pylint will still work however (albeit
not provide the fuzzy title checks).



### Examples
These are examples of errors which biblint will find:

  - Certain underquoted names. For example, this BibTeX title:

	```tex
	title = {How cat pictures on the Internet can be AES-encrypted}
	```

	might have "Internet" and "AES" spelled "internet" and "aes", because
	they're not enclosed in braces. biblint will show this:

	```
	Testerrors.bib:32 (foobar1920dependence): Unquoted abbreviation 'AES' in title. [entries-with-unquoted-abbreviations]
	Testerrors.bib:32 (foobar1920dependence): Unquoted name 'internet' in title. [entries-with-unquoted-names]
	```

  - The other way around, overquoting, is equally wrong. This will also be
	recognized:

	```
	Testerrors.bib:43 (mcnulty2012foobar): Overquoted title. [entries-with-overquoted-title]
	```

  - Month format is expected to be in uniform unquoted three-letter form:

	```
	Testerrors.bib:46 (mcnulty2012foobar): Month was quoted when unquoted expected: jan [entries-with-overquoted-month]
	```

  - Certain special characters included in low-quality BibTeX sources will
	show messed-up in your document. Such characters are, for example,
	typographic quotation marks or dashes. biblint will warn you:

	```
	Testerrors.bib:43 (mcnulty2012foobar): Entry has illegal chars '—' in field 'title'. [entries-with-illegal-chars]
	```

  - The presence of a DOI and the correct DOI URL is plausibilized:

	```
	Testerrors.bib:36 (foobar1920dependence): DOI present, but URL does not point to it. Expect: url = {https://dx.doi.org/10.1109/RADECS.2011.3333333}, [check-uniform-doi-url]
	Testerrors.bib:51 (mcnulty2012fsdf): DOI present, but no URL present at all. Expect: url = {https://dx.doi.org/10.1109/RADECS.2011.6131431}, [check-uniform-doi-url]
	```

  - Duplicate entries within a BibTeX file can lead to unexpected results.
	biblint will warn you:

	```
	Testerrors.bib:1 (miller1920dependence), Testerrors.bib:21 (miller1920dependence): 2 entries for entry with name "miller1920dependence". [duplicate-entries-by-name]
	```

  - ISBN-10 and ISBN-13 numbers will be checked for integrity and the format
	will be asked to be uniform. It will suggest conversion of old ISBN-10
	to new ISBN-13 numbers and recalculate the appropriate checksum value:

	```
	Testerrors.bib:39 (foobar1920dependence): Invalid ISBN, checksum is wrong. [check-isbn]
	Testerrors.bib:50 (mcnulty2012foobar): Old ISBN-10, suggest converting to new ISBN-13 form: 978-1-123-12345-6 [check-isbn]
	Testerrors.bib:61 (mcnulty2012fsdf): ISBN-13 format wrong. Should be nnn-n-nnn-nnnnn-n [check-isbn]
	```



### Full list of implemented checks
To get a complete list of checks that biblint is able to execute, just
run it on the command line wihtout any arguments. Currently, the
implemented checks are:

7 TeX lint checks available:
- **abbreviation-commata**:
      Finds occurences of abbreviations that call for a comma
      immediately after the abbreviation. Examples are 'e.g.' and
      'i.e.'.

- **number-word-hyphen**:
      Finds occurences which are supposed to have a hypen between a
      number and word (e.g., in '32-bit architecture'). May also yield
      false positives (e.g., 'the leftmost 4 bits are').

- **preposition-check**:
      Finds misused prepositions for certain words.

- **repeated-words**:
      Finds text locations which repeat a lot (i.e. more than x
      occurences in y consecutive words).

- **separated-words**:
      Finds occurences where two words are separate that should be
      written as one word (e.g., 'bit stream', 'byte code', 'run
      time').

- **sloppy-abbreviations**:
      Checks sloppy abbreviations such as "don't" or "can't" which
      should be avoided in technical writing.

- **wordiness**:
      Checks wordiness of three-word phrases and offers alternatives.
      For example, "is able to" can be replaced by "can".


18 bibliography lint checks available:
- **check-full-first-names**:
      Checks that author first names are spelled out in full (i.e. not
      abbreviated). An exception to this are RFCs, where first names
      are abbreviated.

- **check-identical-titles**:
      Checks for two titles which are exactly identical for different
      bibliography entries (possible duplicate under two different
      citation names).

- **check-isbn**:
      Checks that the ISBN-10 or ISBN-13 checksum is correct. Checks
      that the format is either n-nnn-nnnnn-n (for ISBN-10) or nnn-n-
      nnn-nnnnn-n (for ISBN-13). Also suggests to convert ISBN-10 to
      ISBN-13 and recalculates the proper ISBN-13 checksum for the
      converted value.

- **check-local-copies**:
      Checks if the referred files are present as local files. It
      checks for files in the localdir command line argument directory
      and checks for both .pdf and .txt files in that directory. It
      will give you a Google search links with arguments that you can
      use to search for a PDF.

- **check-missing-doi**:
      Checks for missing DOIs and tries to heuristically find out if
      it's a IEEE, Springer, ACM or Elsevier publication. For these
      publications, it directly shows a clickable search link that
      should lead to the paper so you can easily find the DOI. Also
      detects DOIs that are potentially present in other metadata
      fields (e.g. "ee") and advises accordingly.

- **check-name-consistency**:
      Checks that author names are consistently written in terms of
      abbreviating their last names. For example, "F. Bar and M. Koo"
      is okay, "Foo Bar and Moo Koo" as well, but the mixing, i.e. "F.
      Bar and Moo Koo" is raised as an error.

- **check-present-fields**:
      Checks that certain fields are present for certain types of
      citations. For example, checks that an "article" has also a
      "journal" set and so on.

- **check-rfc-dois**:
      Checks for RFCs that the DOIs are in the appropriate format as
      specified by RFC 7669 (DOI 10.17487/rfc7669).

- **check-uniform-doi-url**:
      For entries which have a DOI present, checks that the URL points
      to

      ```
      https://dx.doi.org/${doi}
      ```

      An exception are RFCs, which should also have a DOI but a
      different URL. For RFCs, it expects

      ```
      https://tools.ietf.org/rfc/rfc${no}.txt
      ```

      to be set as the URL. RFCs are detected by having a citation
      name of rfc(\d+). This check does not issue any warnings if no
      DOI is present at all.

- **check-uniform-urn-url**:
      For entries which have a URN present, checks that the URL points
      to

      ```
      https://nbn-resolving.org/${urn}
      ```

- **duplicate-entries-by-name**:
      Finds BibTeX entries which have the same cite name. This can
      lead to unexpected results in document and should usually not
      happen.

- **entries-with-illegal-chars**:
      Finds special characters in title or booktitle such as
      typographic quotation marks or typographic dashes which will
      frequently lead to problems during typesetting.

- **entries-with-overquoted-title**:
      Finds overquoted titles. For example, for

      ```tex
      title = {{How To Use The Internet}}
      ```

      it would advise you that there are multiple words in one huge
      curly brace. This might be unintentional.

- **entries-with-unquoted-abbreviations**:
      Finds underquoted abbreviations in the title. For example, if
      the title was set to

      ```tex
      title = {How to use AES}
      ```

      this could become the unintended

      ```tex
      How to use aes
      ```

      if the abbreviation AES was not enclosed by curly braces.

- **entries-with-unquoted-names**:
      Finds unquoted names in the title. For example, a BibTeX entry
      that had

      ```tex
      title = {How to use the Internet}
      ```

      could become the unintended

      ```
      How to use the internet
      ```

      if the word "Internet" was not enclosed by curly braces. This
      only works for a certain hardcoded list of names right now and
      will probably only fit your purpose if you extend the list
      manually by editing the code.

- **misformatted-month**:
      Shows entries with a misformatted month. Months are expected to
      be in unquoted form and use three-letter lowercase English month
      abbreviations (e.g. month = jan, ..., month = dec). This will
      show overquoted months (i.e. {mar} or {{mar}}) which would show
      up wrong in the final document. It will also reject days of the
      week which are encoded in the month field.

- **uncited-citations**:
      When TeX files are given, this check will determine if there are
      citations in the BibTeX which are never cited from the TeX.

- **undefined-citations**:
      When TeX files are given, this check will determine if there are
      undefined citations in the TeX which never appear in the BibTeX.




### Usage
Just run biblint and give it the BibTeX file(s) as argument:

```bash
$ ./biblint my-awesome-phd-thesis.bib
```

It will show you a list of errors on stdout. You can define certain checks to
be performed or not performed, depending on your preference and goals. For
example:

```bash
$ ./biblint -c ALL:-misformatted-month my-awesome-phd-thesis.bib
```

Will perform all checks but the misformatted month check.



### Suppressions
Like any analysis tool, biblint will in some cases throw errors where
everything is perfectly fine. You'll need to tell it that in certain instances
it can calm down and not report anymore. Here's how:

```tex
@manual{fooproc128,
	title = {{FooProcessor128} / {FooProcessor64} datasheet},
	author = {{Foo Semiconductors Inc.}},
	year = {2013},
	month = jun,
	url = {http://www.foosemi.com/datasheet/foorproc128.pdf},
}
```

will lead to a lint warning:

```
Testerrors.bib:64 (fooproc128): No DOI present anywhere in metadata. [check-missing-doi]
```

If you want to explicitly allow it, preface the @manual line by

```tex
% LINT check-missing-doi
```

Multiple such lines can occur after each other to ignore multiple problems.
Also note that you can enter a description after the keyword in order to remind
you why in this instance it was okay to ignore the error

```tex
% LINT check-missing-doi Datasheets by Foo Semiconductors never have DOIs, duh!
```



### VIM integration
biblint is able to export the lists of potential issues in a format that vim
can understand (quickfix). For this, do a biblint run and specify the "errfile"
parameter:

```bash
$ ./biblint -f quickfix -o errors.txt my-awesome-phd-thesis.bib
```

Then open up vi and enter

```vim
:cf errors.txt
```

This will load up the bib file with the first error and jump to it. With :cp or
:cn you can navigate to the previous or next error. For convinience, you could
also edit your ~/.vimrc to include

```vim
imap <F11> <Esc>:cp<Enter>zz:cc<Enter>
map <F11> :cp<Enter>zz:cc<Enter>
imap <F12> <Esc>:cn<Enter>zz:cc<Enter>
map <F12> :cn<Enter>zz:cc<Enter>
```

This will allow you to browse previous/next errors using the F11 or F12
function keys and it will always center the error in the middle of the screen
vertically. You can also easily integrate biblint into Makefiles. For example,
you could use these .PHONY targets biblint and fixlint as an inspiration:

```makefile
.PHONY: biblint fixlint

biblint:
	biblint --only-cited-bibentries -o biblint.err -f quickfix -c 'DEFAULT:-uncited-citations' *.bib *.tex

fixlint:
	vi -c ":set cmdheight=2" -c ":cf biblint.err"
```

### Other uses of biblint
In order to have consistent naming of authors throughout the paper, the names
of all authors and editors can be exported from biblint using the authorscan
action:

```bash
$ ./biblint --action authorscan Testerrors.bib -o authors.json
```

This outputs a JSON file with all authors that appear in any of the
bibliography files. That file in turn can then be run through the included
"lookup_authors_dblp" script, which queries the DBLP against all author names.
The goal is to identify misspelled names (e.g. Jean-Sebastien Coron instead of
the correct Jean-Sébastien Coron) on one side and to get consistent naming on
the other side throughout all types of citations (e.g. if you quote one time as
B. Preneel and the other time as Bart Preneel). For this, simply run the
authors.json through the given script:

```bash
$ ./lookup_authors_dblp authors.json
Richard L Anderson
 -> Richard L Anderson

Ross Anderson
	Alan Ross Anderson
 -> Ross Anderson
	Ross J Anderson
	Ross P Anderson

Andreas G. Andreou
 -> Andreas G Andreou

Adrian Antipa
 -> Adrian Antipa

Kazumaro Aoki
 -> Kazumaro Aoki
```

This means you'll get a list of authors which highlights exact matches
(as indicated by '->').

Note that it'll cache URL queries in a SQLite database
author_scan_cache.sqlite3 in order not to load the DBLP server unnecessarily.
Please not that there's also rate limiting in effect in order to distribute the
DBLP load. I'll politely ask for you not to disable it. I would hate for them
to discontinue their incredibly useful machine-readable interface. Don't ruin
it for everyone, please. :-)



