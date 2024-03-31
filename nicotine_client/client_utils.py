def _search_timeout(self, search):
        """Callback function that is triggered after the timeout elapses"""

        def _post_search_result(self, track_list: list[WebApiSearchResult]):
            try:
                response = self.session.post(f'http://{config.sections["web_api"]["remote_ip"]}:{config.sections["web_api"]["remote_port"]}/response/search/global', 
                                             json=[track.model_dump() for track in track_list])
                return response
            except Exception as ex:
                log.add("Something went wrong when sending the results to the client")

        if not search.token in self.active_searches:
            return
        
        #First thing is to remove the search from the core so that we do not process any other response for that token
        core.search.remove_web_api_search(search.token)
        #Delete the search from dict
        deleted_search = self.active_searches.pop(search.token)

        #filter the items
        filtered_list = [search_result for search_result in deleted_search if self._apply_filters(search_result, search.search_filters)]

        #Send the results based on the input given by the client in the api request
        free_slots_list = []
        if search.smart_filters:
            #Filter first by free slots
            free_slots_list = [file for file in filtered_list if file.has_free_slots]
            
            if len(free_slots_list) > 0:
                #Then order by upload speed
                free_slots_list.sort(key=lambda x: (x.search_similarity, x.ulspeed), reverse=True)
            start = time.time()
            if len(free_slots_list) > 0:
                _post_search_result(self, free_slots_list[:10])
            end = time.time()    

        else:
            start = time.time()
            if len(filtered_list) > 0:
                _post_search_result(self, filtered_list)
            end = time.time()


        print(f"=================================")
        print(f"Original: {len(deleted_search)}")
        print(f"Filtered: {len(filtered_list)}") 
        print(f"Free slots: {len(free_slots_list)}")
        print(f"Exec. time: {end - start}")
        print(f"=================================")

def _apply_filters(self, search, search_filters) -> bool:

    result = None
    if search_filters is not None:
        for filter in search_filters:
            if hasattr(search,filter):
                if getattr(search,filter) == search_filters[filter]:
                    result = True
                else:
                    return False
            else:
                return False
    else:
        return True

    return result
