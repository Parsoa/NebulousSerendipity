#ifndef BED_HPP
#define BED_HPP

#include <string>
#include <sstream>
#include <iostream>
#include <iterator>
#include <algorithm>

using namespace std ;

#define SVTYPE_MISC         uint8_t(0) 
#define SVTYPE_DEL          uint8_t(1)
#define SVTYPE_INS          uint8_t(2)

struct Track {
    uint8_t chrom ;
    uint32_t begin ;
    uint32_t end ;
    uint8_t svtype ;
    uint32_t svlen ;
    string seq ;
} ;

uint8_t get_chromosome_index(string chrom) {
    string ch = chrom.substr(3, chrom.length() - 3) ;
    if (ch == "X") {
        return 22 ;
    }
    if (ch == "Y") {
        return 23 ;
    }
    return std::stoi(ch) ;
}

string get_chromosome_name(uint8_t index) {
    if (index < 22) {
        return "chr" + std::to_string(index) ;
    } else if (index == 22) {
        return "chrX" ;
    } else if (index == 23) {
        return "chrY" ;
    } else {
        return "chrUn" ;
    }
}

int parse_svtype(string svtype) {
    if (svtype == "DEL") {
        return SVTYPE_DEL ;
    }
    if (svtype == "INS") {
        return SVTYPE_INS ;
    }
    return SVTYPE_MISC ;
}

Track parse_track_name(string name) {
    stringstream ss(name) ;
    vector<string> tokens ;
    string token ;
    while (getline(ss, token, '_')) {
        tokens.push_back(token) ;
    }
    int i = tokens[0].find('@') ;
    Track track ;
    track.chrom = get_chromosome_index(tokens[0].substr(i + 1, tokens[0].length() - (i + 1))) ;
    track.begin = stoi(tokens[1]) ;
    track.end = stoi(tokens[2]) ;
    return track ;
}

std::vector<Track> load_tracks_from_file(string path) {
    std::ifstream bed_file(path) ;
    std::string line ;
    int i = 0 ;
    unordered_map<string, int> header ;
    while (std::getline(bed_file, line)) {
        istringstream iss(line) ;
        if (i == 0) {
            if (line[0] != '#') {
                // TODO: error
            }
            vector<string> tokens{istream_iterator<string>{iss}, istream_iterator<string>{}} ;
            for (int i = 0; i < tokens.size(); i++) {
                header[tokens[i]] = i ;
            }
        } else {
            vector<string> tokens{istream_iterator<string>{iss}, istream_iterator<string>{}} ;
            Track track ;
            track.chrom = get_chromosome_index(tokens[0]) ;
            track.begin = std::stoi(tokens[1]) ;
            track.end = std::stoi(tokens[0]) ;
            if (header.find("SVLEN") != header.end()) {
                track.svlen = std::stoi(tokens[header["SVLEN"]]) ;
            }
            if (header.find("SEQ") != header.end()) {
                track.seq = tokens[header["SEQ"]] ;
            }
            if (header.find("SVTYPE") != header.end()) {
                track.svtype = parse_svtype(tokens[header["SEQ"]]) ;
            } else {

            }
        }
    }
}

#endif