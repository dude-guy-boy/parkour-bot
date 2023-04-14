from interactions.ext import paginators as standard_paginator
from interactions import Client

class Paginator(standard_paginator.Paginator):
    @classmethod
    def create_from_string(
        cls,
        client: "Client",
        content: str,
        prefix: str = "",
        suffix: str = "",
        num_lines: int = 10,
        page_size: int = 4000,
        timeout: int = 0,
    ) -> "standard_paginator.Paginator":
        """
        Create a paginator from a list of strings. Useful to maintain formatting.

        Args:
            client: A reference to the client
            content: The content to paginate
            prefix: The prefix for each page to use
            suffix: The suffix for each page to use
            num_lines: The maximum number of lines for each page
            page_size: The maximum number of characters for each page
            timeout: A timeout to wait before closing the paginator

        Returns:
            A paginator system
        """

        num_lines = max(1, num_lines) # Make sure number of lines is at least one
        page_size = max(1, page_size) # Make sure max page length is at least one

        page_lists = cls.__break_lines(cls, lines = content.split("\n"), num_lines = num_lines, page_size = page_size)

        pages = []

        for page in page_lists:
            pages.append(standard_paginator.Page(content="\n".join(page), prefix=prefix, suffix=suffix))

        return cls(client, pages=pages, timeout_interval=timeout)
    
    def __break_lines(self, lines, num_lines, page_size):
        result = []
        page = []
        current_length = 0
        
        for line in lines:
            line_length = len(line) + 1  # Add 1 for the newline character

            # If theres more room on this page, and the line
            # won't cause the page to exceed the max length
            if len(page) < num_lines and current_length + line_length <= page_size:
                page.append(line)
                current_length += line_length

            # If theres more room on the page, but the
            # line is longer than a half page
            elif len(page) < num_lines and line_length > page_size / 2:
                # Fill rest of page with the line
                first, remaining = self.__break_string(self, input_str = line, max_len = (page_size - sum(len(s) for s in page)))
                page.append(first)
                result.append(page)

                # Continue next page with the rest of the line
                page = [remaining]
                current_length = len(remaining)

            # If theres no room left on the page or adding the line would
            # cause the page to exceed its max length
            else:
                result.append(page)
                page = [line]
                current_length = line_length

        result.append(page)
        
        return result
    
    def __break_string(self, input_str, max_len):
        words = input_str.split()
        output_str = ''
        for word in words:
            if len(output_str + ' ' + word) > max_len:
                break
            else:
                output_str += ' ' + word
        remaining_str = input_str[len(output_str):]
        return output_str.strip(), remaining_str.strip()