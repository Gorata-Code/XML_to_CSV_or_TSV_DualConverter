import os
import sys
import csv
from xml.etree import ElementTree as elementTree


def dict_types_files_converter(file_name: str, target_file_type: str) -> None:
    """
    The entry point of our script. Reads a file and converts it to the opposite format based on its current format
    :param file_name: The file to be read and converted
    :param target_file_type: Differentiate between CSV and TSV file types
    :return: None
    """

    print(f'\n\tReading your {os.path.splitext(file_name)[-1][1:].upper()} file...')

    # XML ----> CSV / TSV
    if os.path.splitext(file_name)[-1].casefold() == '.xml':

        # Writing to a CSV / TSV file
        print(f'\n\tWriting your {target_file_type.upper()} file...')

        # Determining the delimiter arg
        delimiter: str = "," if target_file_type.strip() == 'csv' else "\t"

        xml_content: (str, {}) = xml_reader(file_name)  # We access our xml file contents

        # We slice our dictionary and use more slicing as a getter
        column_headers: [str] = [column_header for column_header in xml_content[1][xml_content[0]][0]]

        # We collect each row data as a dictionary and add each dictionary to a list
        full_records: [{}] = [record for record in xml_content[1][xml_content[0]]]

        with open(resource_path(f'../{xml_content[0]}.{target_file_type}'), mode='w', encoding='UTF-8',
                  newline='') as c_tsv_source_file:

            csv_writer: csv.DictWriter = csv.DictWriter(c_tsv_source_file, fieldnames=column_headers,
                                                        delimiter=delimiter)
            csv_writer.writeheader()

            [csv_writer.writerow(row_data) for row_data in full_records]
            print(f'\n\tSUCCESS! Your {target_file_type.upper()} file has been successfully created.')

    # CSV / TSV ----> XML
    elif os.path.splitext(file_name)[-1].casefold() == '.tsv' or os.path.splitext(file_name)[-1].casefold() == '.csv':

        print(f'\n\tWriting your XML file...\n')

        # We read our json data as a dictionary
        data_from_c_tsv: [{}] = csv_tsv_reader(file_name, target_file_type)

        # We use the main key as our root element's tag
        root_tag = os.path.splitext(file_name)[0].replace(" ", "_").replace("(", "").replace(")", "").lower()

        # We create a root (parent) element
        parent_element: elementTree.Element = elementTree.Element(f'{root_tag}')

        # We access each dictionary on the list and add each key as a sub element tag. We also use the first column
        # as a parent element and use its text value as an attribute
        try:
            for record in data_from_c_tsv:
                level_1_sub_element = elementTree.SubElement(parent_element, str(list(data_from_c_tsv[0].keys())[0]))
                level_1_sub_element.set("record_for", f"{record['year']}")

                for record_key, record_value in record.items():
                    if record_key != f'{level_1_sub_element.tag}':  # Excluding the first column as alluded to above
                        level_2_sub_element = elementTree.SubElement(level_1_sub_element, record_key)
                        level_2_sub_element.text = record_value
        except Exception and KeyError:
            if KeyError:
                print(f'\n\tERROR! The file "{file_name}"\'s formatting is incompatible with this script.')
            else:
                raise
            sys.exit(1)

        # We convert our parent element and all its sub elements to an element tree
        final_xml: elementTree = elementTree.ElementTree(parent_element)

        # We write our XMl file
        with open(resource_path(f"../{root_tag}.xml"), mode='wb') as xml_file:
            final_xml.write(xml_file, encoding='UTF-8', xml_declaration=True)

            print(f'\n\tSUCCESS! Your XML file has been successfully created.')


def xml_reader(file_name: str) -> (str, {}):
    """
    Read an xml file and convert its level-2-sub-tags to column headings and their text to row values
    :param file_name: The name of the xml file to be read / converted
    :return: A two value tuple containing the root-tag for naming the new file and a dictionary of all the records
    """

    # We read (parse) our xml file data here
    our_xml_source_file: elementTree = elementTree.parse(resource_path(f"../{file_name}"))

    # We access the main element to serve later as a file name for our resulting csv / tsv file
    parent_element: elementTree.Element = our_xml_source_file.getroot()

    name_of_resulting_file: str = parent_element.tag

    # Initialise a columns container
    columns: [str] = []

    # Retrieve every sub-element of every level_1_sub-element as a Column Heading and add it to a list (w/o duplicates)
    [[(columns.append(book.tag.upper()) if book.tag.upper() not in columns else None) for book in element] for element
     in parent_element]

    # Getting the individual records lists and collecting them in a list
    rows: [list] = []

    try:
        for element in parent_element:
            elements_list: [str] = []  # A self annihilating list to hold each unique element's child elements tags
            rows_temp_list: [] = []  # Another temporary list to hold each sub elements' tags

            for sub_element in element:
                if sub_element.tag not in elements_list:
                    elements_list.append(sub_element.tag)
                    rows_temp_list.append(sub_element.text.replace('\n', '').strip())

                elif sub_element.tag in elements_list:  # This is to account for repeating tags within each sub element

                    # We check if the last sub element's text is already a list. If so, we append the current
                    # sub_element's text to it since they have the same element tag. If it is not already a list we
                    # remove it from the rows temporary list, we then collect it in a new list with the current sub
                    # element's text. Finally, we re-append it to the rows temporary list
                    rows_temp_list[-1].append(sub_element.text.replace('\n', '').strip()) if isinstance(rows_temp_list[-1],
                                                                                                        list) else \
                        rows_temp_list.append(list([rows_temp_list.pop(), sub_element.text]))

            rows.append(rows_temp_list)  # We add each sub element's list of rows to the main rows list of the document
    except Exception and KeyError:
        if KeyError:
            print(f'\n\tERROR! The file "{file_name}"\'s formatting is incompatible with this script.')
        else:
            raise
        sys.exit(1)

    # Make each row into a dictionary with columns as keys and collect the dictionaries in a list
    full_records_list: [{}] = [dict(zip(columns, row)) for row in rows]

    # Add the list of dictionaries to a new dictionary with the root tag as the key
    xml_content: {} = {parent_element.tag: full_records_list}

    return name_of_resulting_file, xml_content


def csv_tsv_reader(file_name: str, delimiter: str) -> [{}]:
    """
    Read content from a CSV / TSV file and return it as a list of dictionary collections
    :param file_name: The name of the data source file to be converted
    :param delimiter: To control how the file is read i.e. whether to use commas (csv) or tabs (tsv) as separators
    :return: A list of dictionaries
    """

    # Setting the delimiter
    delimiter: str = "\t" if delimiter.strip() == 'tsv' else ","

    with open(resource_path(f'../{file_name}'), 'r', encoding='UTF-8') as c_tsv_source_file:
        csv_reader: csv.DictReader = csv.DictReader(c_tsv_source_file, delimiter=delimiter)

        # Retrieve the dict keys into an array
        columns: [str] = csv_reader.fieldnames

        # Get the values and add them to a list of lists
        rows = [list(row.values()) for row in csv_reader]

        # Update our dictionary by mapping key-value pairs and appending them to a list
        t_csv_content: [{}] = [dict(zip(columns, row)) for row in rows]

    return t_csv_content


def resource_path(relative_path) -> [str, bytes]:
    """
    For managing file resources.
    :param: relative_path: The relative path (relative to the script file) of the target file as a string
    :return: A list of bytes (file content) and string (file path)
    """

    base_path: [] = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)
