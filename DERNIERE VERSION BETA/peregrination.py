#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
(c) Copyright Yoan BOUZIN

  This file is part of Pérégrination v1.0.

    Pérégrination v2.0 is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Pérégrination v1.0 is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Pérégrination v2.0.  If not, see <http://www.gnu.org/licenses/>. 2

Source des fichier shapefile belgique et france
http://www.gadm.org/country
"""

##########
# IMPORT #
##########

#pure python
from operator import itemgetter
import collections
import csv
import re
import base64
import webbrowser
# get the correct encoding
import locale
print_encoding =  locale.getdefaultlocale()[1]
#external library
import numpy as np
from matplotlib import cm
from matplotlib import colors
import folium

#############
# FONCTIONS #
#############
def import_town_gps_coord(town_file):
    """
    return dictionary of town with latitude and longitude
    
    input :
        town_file (file) :
            The file generated by Heredis and SQLite Manager. See the documentation to how have the file
            
    output :
        dico_town (dictionary) :
            - key (string) : town_name
            - value (2-element tuple)  : (latitude,longitude)
    """
    lol = csv.reader(open(town_file, 'r'),delimiter=",")
    dico_town = {rows[0]:[float(rows[1]),float(rows[2])] for rows in lol}
    return dico_town

def convert_to_trajectory_GEDCOM(ascdt,town_list,dico_ID,function):
    """
    Convert the dictionnary into a list of trajectory
    Adapted for GEDCOM importation
    
    input :
        ascdt (dictionnary) : the object returned by import_ascendance() function
        town_list (dictionnary) : the object returned by import_town_gps_coord()
        
    output :
        traj : tuple of 7 elements :
            -0 : longitude of the cityA (city of the father/mother)
            -1 : latitude of the cityA (city of the father/mother)
            -2 : longitude of the cityB (city of the sosa)
            -3 : latitude of the cityB (city of the sosa)
            -4 : cityA name
            -5 : cityB name
            -6 : generation of the parents
        coo : tuple of 5 elements contening
            -0 : longitude of the cityA (city of the father/mother)
            -1 : latitude of the cityA (city of the father/mother)
            -2 : longitude of the cityB (city of the sosa)
            -3 : latitude of the ityB (city of the sosa)
            -4 : generation of the parents
    """
    list_traj = list()
    list_coord = list()
    for i in ascdt.keys():
        cityB = ascdt[i][3] #ville de l'individue étudié (point d'arrivé)
        p = ascdt[i][9] #@id@ du père
        m = ascdt[i][10] #@id@ de la mère
        for ID in p,m:
            #get method : if True , they are ID ind dict, if False, no ID : equal to '' or ID but notpresent because descendent genealogy
            if ascdt.get(ID):
                g= ascdt[ID][-1]
                cityA = ascdt[ID][3]
                if cityA != ''  :
                    if cityB != '' :
                        if cityA != cityB:
                            function(text='Génération '.decode("iso8859_15")+str(g)+' : '+ascdt[ID][1].decode("iso8859_15")+' ==> '+ascdt[i][1].decode("iso8859_15"))
                            traj = (town_list[cityA][0],town_list[cityA][1],town_list[cityB][0],town_list[cityB][1],cityA, cityB,g)
                            coo = (town_list[cityA][0], town_list[cityA][1],town_list[cityB][0],town_list[cityB][1],g)
                            list_traj += [traj]
                            list_coord += [coo]
                        #test !! in the case all the city are identical, few city, descendance ??
                        if cityA == cityB:
                            #function(text='Génération '.decode("iso8859_15")+str(g)+' : '+ascdt[ID][1].decode("iso8859_15")+' ==> '+ascdt[i][1].decode("iso8859_15"))
                            traj = (town_list[cityA][0],town_list[cityA][1],town_list[cityB][0],town_list[cityB][1],cityA, cityB,g)
                            coo = (town_list[cityA][0], town_list[cityA][1],town_list[cityB][0],town_list[cityB][1],g)
                            list_traj += [traj]
                            list_coord += [coo]
                #the father/mother of 'i' don't have location, trying to look higher in the pedigree to found a place
                if cityA == '' and  cityB != '':
                    # get @id@ of the grand parents of 'i' (the parents 'ID' of 'i' must exist to this point)
                    liste_ID_before = list()
                    if ascdt[ID][9] != '':
                        liste_ID_before += [ascdt[ID][9]]
                    if ascdt[ID][10] != '':
                        liste_ID_before += [ascdt[ID][10]]
                    # if the liste_ID_before is empty, they are no grand parents, continue
                    # this control are in the case they are no parents in the generation g+1
                    if len(liste_ID_before) == 0:
                        continue
                    else:
                        #we have grand parents, go control their birth places
                        city = False
                        liste_ID_after = list()
                        while city == False:
                            #iterate through the liste_ID_before and get the parents-@id@ for each
                            for id_i in liste_ID_before:
                                if ascdt[id_i][9] != '':
                                    #Store only if the father and child don't have any Place
                                    if ascdt[id_i][3] == '' and ascdt[ascdt[id_i][9]][3] == '':
                                        #store g_N-father ID
                                        liste_ID_after+=[ascdt[id_i][9]]
                                if ascdt[id_i][10] != '':
                                    #Store only if the mother and child don't have any Place
                                    if ascdt[id_i][3] == '' and ascdt[ascdt[id_i][10]][3] == '':
                                        #store g_N-mother ID
                                        liste_ID_after+=[ascdt[id_i][10]]
                            #check point, for the first turn it's not blocked
                            if len(liste_ID_before) == 0:
                                break
                            #analyse each Places for each founded ID
                            else:
                                for prts_i in liste_ID_before:
                                    if prts_i != '':
                                        g= ascdt[prts_i][-1]
                                        cityA = ascdt[prts_i][3]
                                        if cityA != ''  :
                                            if cityA != cityB:
                                                function('Génération '.decode("iso8859_15")+str(g)+' : '+ascdt[prts_i][1].decode("iso8859_15")+' ==> '+ascdt[i][1].decode("iso8859_15"))
                                                traj = (town_list[cityA][0],town_list[cityA][1],town_list[cityB][0],town_list[cityB][1],cityA, cityB,g)
                                                coo = (town_list[cityA][0], town_list[cityA][1],town_list[cityB][0],town_list[cityB][1],g)
                                                list_traj += [traj]
                                                list_coord += [coo]
                                #second check point, if they are no parents-@id@ in the generation g+1, break the loop
                                if len(liste_ID_after) == 0:
                                    break
                                else:
                                    #replace the liste_ID_before by the liste_ID_after and replace liste_ID_after by an empty list
                                    liste_ID_before = liste_ID_after
                                    liste_ID_after = []
    return list(set(list_traj)), list(set(list_coord))
           
def find_min_max_coordinate(list_coord):
    """
    find the minimum and maximum coordinate to trace the map
    and add a value to have a margin on the map

    input :
        list_coord (list) : the 2nd object returned by convert_to_trajectory_ascdt()

    output :
        - x_min (float) : the minimum longitude
        - y_min (float) : the minimum latitude
        - x_max (float) : the maximum longitude
        - y_max (float) : the maximum latitude
        - g_max (integer) : the maximum number of generation
    """
    array = np.asarray(list_coord)
    minimums = array.min(axis=0)
    y1_min, x1_min, y2_min, x2_min, g_min = minimums
    x_min = min(x1_min, x2_min)
    y_min = min(y1_min, y2_min)
    
    maximums = array.max(axis=0)
    y1_max, x1_max, y2_max, x2_max, g_max = maximums
    x_max = max(x1_max, x2_max)
    y_max = max(y1_max, y2_max)
    #after found the min and max I had an extra value to have a margin in the map
    x_min = x_min-0.5
    y_min = y_min-0.5
    x_max = x_max+0.5
    y_max= y_max+0.5
    g_max = int(g_max)
    return y_min, x_min, y_max, x_max, g_max

def find_nth_character(str1, substr, n):
    """
    return the index of the nth querring subtring
    
    input :
        str1 (string) : the string
        substr (string) : the target string
        n (integer) : the nth occurence you looking for
        
    return :
        pos (integer) : index of the substring at the nth position
    """
    pos = -1
    for x in xrange(n):
        pos = str1.find(substr, pos+1)
        if pos == -1:
            return None
    return pos

def codec(strA,strB):
    """
    Find the correct combination of encoding to concatenate two string
    Related to create_annonation_text_gedcom
    input : strA, strB : string to concatenate
    output : concatenation of strA and strB
    """
    try:
        strAB = strA.encode('iso8859_15')+strB
        return strAB
    except:
        try:
            strAB = strA+strB.encode('iso8859_15')
            return strAB
        except:
            try:
                A = strA.decode('iso8859_15') 
                B = strB.decode('iso8859_15')
                strAB = A + B
                return strAB
            except:
                A = strA.encode('iso8859_15') 
                B = strB.encode('iso8859_15')
                strAB = A + B
                return strAB

def multiple_wedding_gedcom(line):
    """
    Separates information from each marriage in independent group.
    In the case of multiple marriage, Hérédis concatenate the event data
    in the same line and uses a bulleted list. This function gathers data on
    the husband / wife, the date and town wedding.

    input :
        line (list) : the line with the multiple wedding
    output :
        list_of_result (list of 3-elements tuple)
            name, date, town

    Using RegEx :

        - to catch only family name
            ((?:(?:particules) )?[capital_letter special_capital_letter symbol]+\b)

            particules : list of particule are :
                d'|de|des|la|DE|VAN|LE

            capital_letter : all the capital letter of the alphabet
                ABCDEFGHIJKLMNOPQRSTUVWXYZ

            special_capital_letter : special letter for foreign familly names
                ÀÁÂÄÃÅĄĆČĖĘÈÉÊËÌÍÎÏĮŁŃÒÓÔÖÕØÙÚÛÜŲŪŸÝŻŹÑßÇŒÆČŠŽ∂ð
                
            other_symbol : generally used for composed familly names or to show variation
                , . / ( ) -
    
        - to cath only town
            (?!\s)[\w\s-]+(?<!\s)

        - to catch only years
            [0-9]{4}
    """
    list_of_result = list()
    splitted_names  =  line[4].split('\x95')
    splitted_dates  =  line[5].split('\x95')
    splitted_towns  =  line[6].split('\x95')
    data = zip(splitted_names, splitted_dates, splitted_towns)
    for ndt in data:
        n, d, t = ndt
        names_result = " ".join(re.findall(ur"((?:(?:d'|de|des|la|DE|VAN|LE) )?[A-ZÀÁÂÄÃÅĄĆČĖĘÈÉÊËÌÍÎÏĮŁŃÒÓÔÖÕØÙÚÛÜŲŪŸÝŻŹÑßÇŒÆČŠŽ∂ð,.'-\(\)/]+\b)",unicode(n.decode('iso8859-15')),re.UNICODE))
        date_result = "".join(re.findall(r"[0-9]{4}",d))
        if t:
            if t[-1].isspace():
                town_result = t[1:len(t)-1]
            elif t[0].isspace():
                town_result = t[1:]
        else:
            town_result = ''
        #town_result = "".join(re.findall(ur"(?!\s)[\w\s-]+(?<!\s)",unicode(t.decode('iso8859-15')),re.UNICODE))
        if names_result == '' and date_result == '' and town_result == '':
            continue
        else:
            #list_of_result += [(names_result,date_result,town_result)] #avant       
            list_of_result += [(names_result,date_result,town_result)] #test town_result with no encode
    return list_of_result

def generate_map_gedcom(typ,y_min, x_min, y_max, x_max,g_max,list_traj,dico_annotation, popup_trajectory, filename, shapefile):
    """
    Generate Open Street Map HTML page
    """
    xmean = np.mean([x_min,x_max])
    ymean = np.mean([y_min,y_max])
    if typ == 1:
        list_traj = sorted(list_traj, key=itemgetter(6), reverse=True)
    elif typ == 2:
        list_traj = sorted(list_traj, key=itemgetter(6), reverse=True)
    my_map1 = folium.Map(location=[ymean,xmean],tiles='Stamen Terrain',zoom_start=6)
    my_map2 = folium.Map(location=[ymean,xmean],zoom_start=6)
    for my_map in my_map1, my_map2:
        town_set = set()
        dico_traj_size = dict()
        #create step color map
        hexa_colors = list()
        for g in range(1, g_max+1):
            cm_object = cm.Paired(1.*g/g_max)
            rgb = cm_object[:3]
            hexa = colors.rgb2hex(rgb)
            hexa_colors.append(hexa)
        #make legend
        #colormap = folium.colormap.linear.Paired.scale(1, g_max).to_step(g_max)
        colormap = folium.colormap.StepColormap(hexa_colors, index=None, vmin=1.0, vmax=float(g_max), caption= u"Générations")
        my_map.add_child(colormap)
        #make shapefile (only if its in group mode)
        if shapefile:
            my_map.choropleth(geo_path='data_tmp.json',fill_color='red')
        nb_polyline = dict()
        #dico to store the town description and avoid overlap of marker when
        dico_pop = dict()
        dico_size = dict()
        for data in list_traj:
            y1,x1,y2,x2,m1,m2,g= data
            
            #polyline
            if ((y1,x1),(y2,x2)) not in nb_polyline.keys():
                nb_polyline[(y1,x1),(y2,x2)] = 1
            else:
                nb_polyline[(y1,x1),(y2,x2)] += 1
                
            for y, x, m, g in (y1,x1,m1,g),(y2,x2,m2,g):
                try:
                    pop = m.decode('iso8859_15')+"\n"+dico_annotation[m][0].decode('iso8859_15')
                except UnicodeEncodeError:
                    pop = m.decode('iso8859_15')+"\n"+dico_annotation[m][0]
                if (y,x) not in dico_pop.keys():
                    pop_ad = set()
                    pop_ad.add(pop)
                    dico_pop[(y,x)] = pop_ad
                else:
                    pop_ad = dico_pop[(y,x)]
                    pop_ad.add(pop)
                    dico_pop[(y,x)] = pop_ad
                #generation polyline marker size
                if (y,x) not in dico_size.keys():
                    dico_size[(y,x)]=[g]
                else:
                    if g not in dico_size[(y,x)]:
                        dico_size[(y,x)] += [g]
        for data in list_traj:
            #data
            y1,x1,y2,x2,m1,m2,g= data           
            #get color
            cm_object = cm.Paired(1.*g/g_max)
            rgb = cm_object[:3]
            hexa = colors.rgb2hex(rgb)
            #trajectory
            #avoid when trajectory have the same start/end location
            #it's happened when subdivision are not found and the level is "town" location level
            if (y1,x1) != (y2,x2):
                for key in (y1,x1), (y2,x2):
                    sorted_g = sorted(dico_size[(key)])
                    size = (sorted_g.index(g) + 1) * 10
                    folium.PolyLine([key,key], color=hexa, weight=size, opacity=0.9).add_to(my_map)
                folium.PolyLine([(y1,x1),(y2,x2)], popup=popup_trajectory[(m1,m2)].decode('iso8859_15') , color=hexa, weight=nb_polyline[(y1,x1),(y2,x2)]*5, opacity=0.9).add_to(my_map)
                nb_polyline[(y1,x1),(y2,x2)] -= 1
            else:
                sorted_g = sorted(dico_size[(y1,x1)])
                size = (sorted_g.index(g) + 1) * 10
                folium.PolyLine([(y1,x1),(y1,x1)], color=hexa, weight=size, opacity=0.9).add_to(my_map)
            #marker
            if (y1,x1) not in town_set:
                folium.Marker([y1, x1], popup=' '.join(list(dico_pop[(y1,x1)]))).add_to(my_map)
                town_set.add((y1,x1))
            if (y2,x2) not in town_set:
                folium.Marker([y2, x2], popup=' '.join(list(dico_pop[(y2,x2)]))).add_to(my_map)
                town_set.add((y2, x2))
        for key, (text, y, x) in dico_annotation.items():
            if (y,x) not in town_set:
                icon = folium.Icon(color=u'black')
                town_set.add(key)
                try:
                    folium.Marker([y,x], popup=key.decode('iso8859_15')+"\n"+text.decode('iso8859_15'), icon=icon).add_to(my_map)
                except UnicodeEncodeError:
                    folium.Marker([y,x], popup=key+"\n"+text, icon=icon).add_to(my_map)
    filename1 = filename.replace(' ','_').replace('.ged','')+'_map_'+str(typ)+'_1.html'
    filename2 = filename.replace(' ','_').replace('.ged','')+'_map_'+str(typ)+'_2.html'
    my_map1.save(filename1)
    my_map2.save(filename2)
    webbrowser.open(filename1)
    webbrowser.open(filename2)
