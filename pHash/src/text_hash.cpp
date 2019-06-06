/*** Author: Jianqi Chen. Jun 2019 ***/
#include <stdio.h>
#include <stdlib.h>
#include "pHash.h"

int main(int argc, char **argv){

    int i,j,k, unseen;
    if (argc < 2){
        printf("not enough input args\n");
        return 1;
    }
    const char *file1 = argv[1];

    printf("file: %s\nPerceptual hashing...\n", file1);
    int nbhashes1 = 0;
    TxtHashPoint *hash1 = ph_texthash(file1,&nbhashes1);
    if (!hash1){
        printf("unable to complete text hash function\n");
        return 1;
    }
    if (nbhashes1 == 0){
        printf("Text is too short to generate a hash.\n");
        return 1;
    }
    
    // print out all info in hash.info, and only unrepeated 32 bits hash in hash file
    // it seems the last 32bits of the 64-bit hash will be 0x00000000 anyway, just remove it.
    FILE *fptr1 = fopen("hash.info","w");
    FILE *fptr2 = fopen("hash","w");
    if (fptr1==NULL || fptr2==NULL){
        printf("Could not open file: hash, hash.info\n");
        return 1;
    }
    
    j = 0; // number of unrepeated hashes
    unsigned long long *all_hashes = (unsigned long long*)malloc( nbhashes1*sizeof(unsigned long long) );
    fprintf(fptr1,"length %d\n", nbhashes1);
    for (i=0;i<nbhashes1;i++){
        unseen = 1;
        fprintf(fptr1,"hash[%d] index: %d\n",i,hash1[i].index);
        fprintf(fptr1,"hash[%d] hash: %llx\n",i,hash1[i].hash);
        fprintf(fptr2,"%x\n",(unsigned int)(hash1[i].hash>>32) ); // comment this line if only print unrepeated hashes.
        for(k=0;k<j;k++){
            if(all_hashes[k]==hash1[i].hash){
                unseen = 0;
                break;
            }
        }
        if(unseen == 1){
            all_hashes[j] = hash1[i].hash;
            j++;
        }   
    }
    fclose(fptr1);
    
//  only print unrepeated hashes (not useful when calculate avg. hamming distance)  
//    for (i=0; i<j; i++)
//        fprintf( fptr2, "%x\n",(unsigned int)(all_hashes[i]>>32) );
        
    fclose(fptr2);

    return 0;
}