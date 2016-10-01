import struct
import mmap

from .tools import WrongTypeException
from .header import Header
from . import photonbunches as pb

from .iact import iact_types

known_types = {}
known_types.update(iact_types)


class EventIOFile(object):

    def __init__(self, path, debug=False):
        self.__file = open(path, 'rb')
        self.__mm = mmap.mmap(self.__file.fileno(), 0, prot=mmap.PROT_READ)
        self.__header_list = []

        self.run_header = self.__read_run_header()
        self._make_complete_header_list()
        self._make_reuse_header_list()
        self.__mm.seek(0)
        self.__read_run_header()

    @property
    def header_list(self):
        return self.__header_list


    def _make_complete_header_list(self):
        while True:
            try:
                header = self.__get_and_save_header()
            except struct.error:
                break
            self.__mm.seek(header.length, 1)

    def _make_reuse_header_list(self):
        for i, h in enumerate(self.__header_list[:]):
            if h.type == 1204:
                self.__mm.seek(h.tell)
                photon_bunch_headers = read_type_1204(self.__mm, h, headers_only=True)
                self.__header_list[i] = (h, photon_bunch_headers)

    def __get_and_save_header(self, expect_type=None):
        header = Header(self.__mm)
        if expect_type is not None:
            if header.type != expect_type:
                header_length = 4 if not header.extended else 5
                self.__mm.seek(header_length * -4, 1)
                raise WrongTypeException(
                    'expected ', expect_type,
                    ', got:', header.type
                )

        return header

    def __get_type(self, type):
        header = self.__get_and_save_header(expect_type=type)
        return known_types[type](self.__mm, header)

    def __read_run_header(self):
        rh = self.__get_type(1200)
        rh['input_card'] = self.__get_type(1212)
        rh['tel_pos'] = self.__get_type(1201)

        return rh

    def __read_event_header(self):
        self.current_event_header = self.__get_type(1202)
        self.current_event_header['telescope_offsets'] = self.__get_type(1203)

    def __iter__(self):
        return self

    def __next__(self):
        return self.next()

    def next(self):
        while True:
            try:
                return pb.PhotonBundle(self.__mm)
            except WrongTypeException:
                pass

            try:
                _ = self.__get_and_save_header(expect_type=1204)
                # simply get rid of the 1204-inter-reuse-stuff.
            except (WrongTypeException, ValueError):
                pass

            try:
                self.__read_event_header()
            except (WrongTypeException, ValueError):
                pass

            try:
                self.last_event_end = self.__get_type(1209)
            except (WrongTypeException, ValueError):
                pass

            try:
                self.run_end = self.__get_type(1210)
                raise StopIteration
            except (WrongTypeException, ValueError):
                pass


class EventIOFileStream(object):

    def __init__(self, path, debug=False):
        self.__file = open(path, 'rb')
        self.__mm = mmap.mmap(self.__file.fileno(), 0, prot=mmap.PROT_READ)

        self.run_header = self.__read_run_header()

    def __read_run_header(self):
        rh = self._retrieve_payload_of_type(1200)
        rh['input_card'] = self._retrieve_payload_of_type(1212)
        rh['tel_pos'] = self._retrieve_payload_of_type(1201)
        return rh

    def _retrieve_payload_of_type(self, type):
        header = self.__get_header(expect_type=type)
        return known_types[type](self.__mm, header)

    def __get_header(self, expect_type):
        header = Header(self.__mm)
        if header.type != expect_type:
            header_length = 4 if not header.extended else 5
            self.__mm.seek(header_length * -4, 1)
            raise WrongTypeException(
                'expected ', expect_type,
                ', got:', header.type
            )
        return header

    def __iter__(self):
        return self

    def __next__(self):
        return self.next()

    def next(self):
        while True:
            try:
                return pb.PhotonBundle(self.__mm)
            except WrongTypeException:
                pass

            try:
                _ = self.__get_header(expect_type=1204)
                # simply get rid of the 1204-inter-reuse-stuff.
            except (WrongTypeException, ValueError):
                pass

            try:
                self.__read_event_header()
            except (WrongTypeException, ValueError):
                pass

            try:
                self.last_event_end = self._retrieve_payload_of_type(1209)
            except (WrongTypeException, ValueError):
                pass

            try:
                self.run_end = self._retrieve_payload_of_type(1210)
                raise StopIteration
            except (WrongTypeException, ValueError):
                pass

    def __read_event_header(self):
        self.current_event_header = self._retrieve_payload_of_type(1202)
        self.current_event_header['telescope_offsets'] = self._retrieve_payload_of_type(1203)
