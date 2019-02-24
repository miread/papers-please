import re


class Inspector:

    def __init__(self):

        self.allowed_nations = []
        self.reqd_vacs = {}
        self.require_passport = False
        self.require_access = False
        self.work_pass_req = False
        self.id_reqd = False
        self.reqs = {}
        self.wanted = ""

    def receive_bulletin(self, criteria):
        print(criteria)

        passport_check = re.compile(r'Entrants require passport')
        if passport_check.search(criteria) is not None:
            self.require_passport = True

        permit_check = re.compile(r'Foreigners require access permit')
        if permit_check.search(criteria) is not None:
            self.require_access = True

        id_check = re.compile(r'Citizens of Arstotzka require ID card')
        if id_check.search(criteria) is not None:
            self.id_reqd = True

        work_check = re.compile(r'Workers require work pass')
        if work_check.search(criteria) is not None:
            self.work_pass_req = True

        allowed_update = re.compile(r'(Allow citizens of )(.+)')
        if allowed_update.search(criteria) is not None:
            clist = allowed_update.search(criteria).group(2).split(", ")
            for item in clist:
                if item not in self.allowed_nations:
                    self.allowed_nations.append(item)

        denied_update = re.compile(r'(Deny citizens of )(.+)')
        if denied_update.search(criteria) is not None:
            clist = denied_update.search(criteria).group(2).split(", ")
            for item in clist:
                if item in self.allowed_nations:
                    self.allowed_nations.remove(item)

        criminal_check = re.compile(r'(Wanted by the State: )([A-Za-z]+)( )([A-Za-z]+)')
        if criminal_check.search(criteria) is not None:
            self.wanted = criminal_check.search(criteria).group(4) + ", " + criminal_check.search(criteria).group(2)

        vacs_read = re.compile(
            r'(Citizens of |Entrants )([A-Za-z, ]+)?(no longer )?(require )([A-Za-z, ]+)(vaccination)')
        match = vacs_read.finditer(criteria)
        for i in match:
            if i.group(1) == "Entrants " and i.group(2) == "no longer ":  # Entrants no longer
                print(i.group(0) + "!1")
                if i.group(5).strip() in self.reqd_vacs:
                    self.reqd_vacs.pop(i.group(5).strip())
            elif i.group(1) == "Entrants " and i.group(
                    4) == "require ":  # Entrants require
                self.reqd_vacs[i.group(5).strip()] = "All"
                print(i.group(0) + "!2")
            elif i.group(1) == "Citizens of " and i.group(3) == "no longer ":  # Citizens of x no longer
                if i.group(5).strip() in self.reqd_vacs:
                    country_list = self.reqd_vacs[i.group(5).strip()].split(", ")
                    matches = set(country_list).intersection(i.group(2).strip().split(", "))
                    for m in matches:
                        country_list.remove(m)
                    self.reqd_vacs[i.group(5).strip()] = ', '.join(country_list)
                    print(i.group(0) + "!3")
            elif i.group(1) == "Citizens of " and i.group(4) == "require ":  # Citizens of x require
                print(i.group(0) + "!4")
                if i.group(5).strip() in self.reqd_vacs:
                    country_list = self.reqd_vacs[i.group(5).strip()].split(", ")
                    matches = i.group(2).strip().split(", ")
                    for m in matches:
                        country_list.append(m)
                    self.reqd_vacs[i.group(5).strip()] = ', '.join(country_list)

    def inspect(self, person):

        name, idn, dob, sex, nat, exp_docs, mismatch = None, None, None, None, None, [], False
        mis_data, wanted_flag, vacs, missing_reqd_vac, has_access = "", False, [], False, False
        has_id, bad_auth, is_worker, has_work_pass = False, False, False, False
        has_vac_cert, vac_cert_reqd = False, False

        exp_check = re.compile(r'(EXP: )(\d{4}.\d{2}.\d{2})')
        name_check = re.compile(r'(NAME: )([A-Za-z]+, [A-Za-z]+)')
        idn_check = re.compile(r'(ID#: )([A-Z0-9]{5}-[A-Z0-9]{5})')
        dob_check = re.compile(r'(DOB: )(\d{4}.\d{2}.\d{2})')
        sex_check = re.compile(r'(SEX: )([A-Z])')
        nat_check = re.compile(r'(NATION: )([A-Za-z ]+)')
        vac_check = re.compile(r'(VACCINES: )([A-Za-z, ]+)')

        for document in person:
            if exp_check.search(person[document]) is not None:
                date = exp_check.search(person[document]).group(2).split('.')
                if int(date[0]) < 1982:
                    exp_docs.append(document.replace("_", " "))
                elif int(date[0]) > 1982:
                    pass
                else:
                    if int(date[1]) < 11:
                        exp_docs.append(document.replace("_", " "))
                    elif int(date[1]) > 11:
                        pass
                    else:
                        if int(date[2]) <= 22:
                            exp_docs.append(document.replace("_", " "))

            if document == "certificate_of_vaccination":
                match = vac_check.search(person[document])
                vacs = [x for x in match.group(2).split(", ")]
                has_vac_cert = True

            if document == "ID_card":
                has_id = True
                print(document, person[document])
            if document == "access_permit":
                has_access = True
                work_check = re.compile(r'(PURPOSE: )([A-Z]+)')
                if work_check.search(person[document]).group(2) == "WORK":
                    is_worker = True
                print(document, person[document])
            if document == "work_pass":
                has_work_pass = True
                print(document, person[document])
            if document == "grant_of_asylum":
                has_access = True
                print(document, person[document])
            if document == "diplomatic_authorization":
                has_access = True
                auth_check = re.compile(r'(ACCESS: )([A-Za-z, ]+)')
                countries = auth_check.search(person[document]).group(2).split(", ")
                if "Arstotzka" not in countries:
                    bad_auth = True
                print(document, person[document])

            if name_check.search(person[document]) is not None:
                if name is not None and name_check.search(person[document]).group(2) != name:
                    mis_data = "name mismatch."
                    mismatch = True
                name = name_check.search(person[document]).group(2)
                if name == self.wanted:
                    wanted_flag = True

            if idn_check.search(person[document]) is not None:
                if idn is not None and idn_check.search(person[document]).group(2) != idn:
                    mis_data = "ID number mismatch."
                    mismatch = True
                idn = idn_check.search(person[document]).group(2)

            if dob_check.search(person[document]) is not None:
                if dob is not None and dob_check.search(person[document]).group(2) != dob:
                    mis_data = "date of birth mismatch."
                    mismatch = True
                dob = dob_check.search(person[document]).group(2)

            if sex_check.search(person[document]) is not None:
                if sex is not None and sex_check.search(person[document]).group(2) != sex:
                    mis_data = "Sex mismatch."
                    mismatch = True
                sex = sex_check.search(person[document]).group(2)

            if nat_check.search(person[document]) is not None:
                if nat is not None and nat_check.search(person[document]).group(2) != nat:
                    mis_data = "nationality mismatch."
                    mismatch = True
                nat = nat_check.search(person[document]).group(2)

        if len(self.reqd_vacs) > 0:
            vac_cert_reqd = True
            for x, y in self.reqd_vacs.items():
                if y == "All" and x not in vacs:
                    missing_reqd_vac = True
                elif nat in y.split(", ") and x not in vacs:
                    missing_reqd_vac = True

        if nat == "Arstotzka":
            has_access = True

        if wanted_flag is True:
            return "Detainment: Entrant is a wanted criminal."

        if mismatch is True:
            return "Detainment: " + mis_data

        if len(exp_docs) > 0:
            return "Entry denied: " + exp_docs[0] + " expired."

        if self.require_passport is True and "passport" not in person:
            return "Entry denied: missing required passport."

        if self.require_access is True and has_access is False:
            return "Entry denied: missing required access permit."

        if self.id_reqd is True and nat == "Arstotzka":
            if has_id is False:
                return "Entry denied: missing required ID card."

        if self.work_pass_req is True and is_worker is True:
            if has_work_pass is False:
                return "Entry denied: missing required work pass."

        if bad_auth is True:
            return "Entry denied: invalid diplomatic authorization."

        if nat not in self.allowed_nations:
            return "Entry denied: citizen of banned nation."

        if vac_cert_reqd is True and has_vac_cert is False:
            return "Entry denied: missing required certificate of vaccination."

        if missing_reqd_vac is True:
            return "Entry denied: missing required vaccination."

        if nat == "Arstotzka":
            return "Glory to Arstotzka."
        else:
            return "Cause no trouble."
