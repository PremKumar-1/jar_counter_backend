from rest_framework.pagination import PageNumberPagination
from rest_framework.utils.urls import replace_query_param, remove_query_param

class RelativeUrlPagination(PageNumberPagination):
    def get_next_link(self):
        if not self.page.has_next():
            return None
        url = replace_query_param(self.request.path, self.page_query_param, self.page.next_page_number())
        for param, value in self.request.query_params.items():
            if param != self.page_query_param:
                url = replace_query_param(url, param, value)
        return remove_query_param(url, self.page_query_param)

    def get_previous_link(self):
        if not self.page.has_previous():
            return None
        url = replace_query_param(self.request.path, self.page_query_param, self.page.previous_page_number())
        for param, value in self.request.query_params.items():
            if param != self.page_query_param:
                url = replace_query_param(url, param, value)
        return remove_query_param(url, self.page_query_param)
