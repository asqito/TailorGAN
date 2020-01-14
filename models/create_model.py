import os
import torch
import torch.nn as nn
from models import network_revised

def create_collar_model(opt):
    model = TailorGAN(opt)
    print("model [%s] was created." % (model.name()))
    return model

def create_sleeve_model(opt):
    model = SleeveGAN(opt)
    print("model [%s] was created." % (model.name()))
    return model

def create_classifier_model(opt):
    model = ClassifierModel(opt)
    print("model [%s] was created." % (model.name()))
    return model


class ClassifierModel(nn.Module):
    def name(self):
        return 'Classifier'

    def __init__(self, opt):
        super(ClassifierModel, self).__init__()
        self.isTrain = opt.isTrain
        if opt.type_classifier == 'collar':
            self.classifier = network_revised.define_classifier(opt.num_collar)
        else:
            self.classifier = network_revised.define_classifier(opt.num_sleeve)
        if self.isTrain:
            self.loss = nn.CrossEntropyLoss()
            self.optimizer = torch.optim.Adam(self.classifier.parameters(), lr=opt.lr, betas=(opt.beta1, 0.999))
        else:
            if opt.type_classifier == 'collar':
                self.classifier.load_state_dict(torch.load('./checkpoints/classifier/path/classifier_%s_50.pth'
                                                           % opt.type_classifier,
                                                           map_location="cuda:%d" % opt.gpuid))
            else:
                self.classifier.load_state_dict(torch.load('./checkpoints/classifier/path/classifier_%s_50.pth'
                                                           % opt.type_classifier,
                                                           map_location="cuda:%d" % opt.gpuid))
            print('Model load successful!')


class Tailor(nn.Module):
    def name(self):
        return 'Tailor'

    def __init__(self, opt):
        super(Tailor, self).__init__()
        self.isTrain = opt.isTrain
        self.netG = network_revised.define_netG(norm='instance', n_blocks=opt.n_blocks,
                                                use_dropout=opt.use_dropout)
        if self.isTrain:
            if opt.step == 'step2':
                self.netG.load_state_dict(torch.load(
                    './checkpoints/TailorGAN_Garmentset/path/collarG/Recon/TailorGAN_Garment_collar_recon_%s.pth' % opt.num_epoch,
                    map_location="cuda:%d" % opt.gpuid
                ))
                self.netD = network_revised.define_discriminator(opt.num_collar, input_nc=3, ndf=32, n_layers_D=3,
                                                                 norm='instance', num_D=1)
                self.optimizer_netD = torch.optim.Adam(self.netD.parameters(), lr=opt.lr * 3, betas=(opt.beta1, 0.999))

                print('Model load successful!')

            self.optimizer_netG = torch.optim.Adam(self.netG.parameters(), lr=opt.lr, betas=(opt.beta1, 0.999))

            self.class_loss = nn.CrossEntropyLoss()
            self.recon_loss = network_revised.vggloss(opt)
            self.concept_loss = nn.L1Loss().cuda(opt.gpuid)
            self.VGGloss = network_revised.vggloss(opt)
            self.adv_loss = network_revised.GANLOSS()
        else:
            self.netG.load_state_dict(torch.load(
                './checkpoints/TailorGAN_Garmentset/path/collarG/Syn/TailorGAN_Garment_syn_netG_12.pth',
                map_location="cuda:%d" % opt.gpuid
            ))

class TailorGAN(nn.Module):
    def name(self):
        return 'TailorGAN'

    def __init__(self, opt):
        super(TailorGAN, self).__init__()
        self.isTrain = opt.isTrain
        self.srcE = network_revised.define_srcEncoder(norm='instance')
        self.edgeE = network_revised.define_edgeEncoder(norm='instance')
        self.netG = network_revised.define_generator('instance', opt.n_blocks, opt.use_dropout)
        if self.isTrain:
            if opt.step == 'step2':
                self.srcE.load_state_dict(torch.load(
                    './checkpoints/TailorGAN_Garmentset/path/collarRecon/TailorGAN_Garment_recon_srcE_%s.pth' % opt.num_epoch,
                    map_location="cuda:%d" % opt.gpuid
                ))
                # for param in self.srcE.parameters():
                #     param.requires_grad = False
                self.edgeE.load_state_dict(torch.load(
                    './checkpoints/TailorGAN_Garmentset/path/collarRecon/TailorGAN_Garment_recon_edgeE_%s.pth' % opt.num_epoch,
                    map_location="cuda:%d" % opt.gpuid
                ))
                # for param in self.edgeE.parameters():
                #     param.requires_grad = False
                self.netG.load_state_dict(torch.load(
                    './checkpoints/TailorGAN_Garmentset/path/collarRecon/TailorGAN_Garment_recon_netG_%s.pth' % opt.num_epoch,
                    map_location="cuda:%d" % opt.gpuid
                ))
                self.netD = network_revised.define_discriminator(opt.num_collar, input_nc=3, ndf=32, n_layers_D=3,
                                                                 norm='instance', num_D=1)
                self.optimizer_netD = torch.optim.Adam(self.netD.parameters(), lr=opt.lr*3, betas=(opt.beta1, 0.999))

                print('Model load successful!')
            if opt.enable_classifier:
                if opt.type_classifier == 'collar':
                    self.classifier = network_revised.define_classifier(opt.num_collar)
                else:
                    self.classifier = network_revised.define_classifier(opt.num_sleeve)
                self.classifier.load_state_dict(torch.load('./checkpoints/classifier/path/classifier_%s_50.pth'
                                                       % opt.type_classifier,
                                                       map_location="cuda:%d" % opt.gpuid))
                for param in self.classifier.parameters():
                    param.requires_grad = False
            self.optimizer_srcE = torch.optim.Adam(self.srcE.parameters(), lr=opt.lr, betas=(opt.beta1, 0.999))
            self.optimizer_edgeE = torch.optim.Adam(self.edgeE.parameters(), lr=opt.lr, betas=(opt.beta1, 0.999))
            self.optimizer_netG = torch.optim.Adam(self.netG.parameters(), lr=opt.lr, betas=(opt.beta1, 0.999))

            self.class_loss = nn.CrossEntropyLoss()
            self.recon_loss = network_revised.vggloss(opt)
            self.concept_loss = nn.L1Loss()
            self.VGGloss = network_revised.vggloss(opt)
            self.adv_loss = network_revised.GANLOSS()
        else:
            self.edgeE.load_state_dict(torch.load(
                    './checkpoints/TailorGAN_Garmentset/path/collarReconLeave1out/TailorGAN_Garment_recon_edgeE_%s.pth' % opt.num_epoch,
                    map_location="cuda:%d" % opt.gpuid
            ))
            self.srcE.load_state_dict(torch.load(
                './checkpoints/TailorGAN_Garmentset/path/collarReconLeave1out/TailorGAN_Garment_recon_srcE_%s.pth' % opt.num_epoch,
                map_location="cuda:%d" % opt.gpuid
            ))
            self.netG.load_state_dict(torch.load(
                './checkpoints/TailorGAN_Garmentset/path/collarReconLeave1out/TailorGAN_Garment_recon_netG_%s.pth' % opt.num_epoch,
                map_location="cuda:%d" % opt.gpuid
            ))



class SleeveGAN(nn.Module):
    def name(self):
        return 'TailorGAN'

    def __init__(self, opt):
        super(SleeveGAN, self).__init__()
        self.isTrain = opt.isTrain
        self.srcE = network_revised.define_srcEncoder(norm='instance')
        self.edgeE = network_revised.define_edgeEncoder(norm='instance')
        self.netG = network_revised.define_generator('instance', opt.n_blocks, opt.use_dropout)
        if self.isTrain:
            if opt.step == 'step2':
                self.srcE.load_state_dict(torch.load(
                    './checkpoints/TailorGAN_Garmentset/path/sleeveRecon/TailorGAN_Garment_recon_srcE_%s.pth' % opt.num_epoch,
                    map_location="cuda:%d" % opt.gpuid
                ))
                # for param in self.srcE.parameters():
                #     param.requires_grad = False
                self.edgeE.load_state_dict(torch.load(
                    './checkpoints/TailorGAN_Garmentset/path/sleeveRecon/TailorGAN_Garment_recon_edgeE_%s.pth' % opt.num_epoch,
                    map_location="cuda:%d" % opt.gpuid
                ))
                # for param in self.edgeE.parameters():
                #     param.requires_grad = False
                self.netG.load_state_dict(torch.load(
                    './checkpoints/TailorGAN_Garmentset/path/sleeveRecon/TailorGAN_Garment_recon_netG_%s.pth' % opt.num_epoch,
                    map_location="cuda:%d" % opt.gpuid
                ))
                self.netD = network_revised.define_discriminator(opt.num_sleeve, input_nc=3, ndf=32, n_layers_D=3,
                                                                 norm='instance', num_D=1)
                self.optimizer_netD = torch.optim.Adam(self.netD.parameters(), lr=opt.lr, betas=(opt.beta1, 0.999))

                print('Model load successful!')
            if opt.enable_classifier:
                if opt.type_classifier == 'collar':
                    self.classifier = network_revised.define_classifier(opt.num_collar)
                else:
                    self.classifier = network_revised.define_classifier(opt.num_sleeve)
                self.classifier.load_state_dict(torch.load('./checkpoints/classifier/path/classifier_%s_50.pth'
                                                       % opt.type_classifier,
                                                       map_location="cuda:%d" % opt.gpuid))
                for param in self.classifier.parameters():
                    param.requires_grad = False
            self.optimizer_srcE = torch.optim.Adam(self.srcE.parameters(), lr=opt.lr, betas=(opt.beta1, 0.999))
            self.optimizer_edgeE = torch.optim.Adam(self.edgeE.parameters(), lr=opt.lr, betas=(opt.beta1, 0.999))
            self.optimizer_netG = torch.optim.Adam(self.netG.parameters(), lr=opt.lr, betas=(opt.beta1, 0.999))

            self.class_loss = nn.CrossEntropyLoss()
            self.recon_loss = nn.L1Loss(opt)
            self.concept_loss = nn.L1Loss()
            self.VGGloss = network_revised.vggloss(opt)
            self.adv_loss = network_revised.GANLOSS()
        else:
            self.edgeE.load_state_dict(torch.load(
                    './checkpoints/TailorGAN_Garmentset/path/sleeveRecon/TailorGAN_Garment_recon_edgeE_%s.pth' % opt.num_epoch,
                    map_location="cuda:%d" % opt.gpuid
            ))
            self.srcE.load_state_dict(torch.load(
                './checkpoints/TailorGAN_Garmentset/path/sleeveRecon/TailorGAN_Garment_recon_srcE_%s.pth' % opt.num_epoch,
                map_location="cuda:%d" % opt.gpuid
            ))
            self.netG.load_state_dict(torch.load(
                './checkpoints/TailorGAN_Garmentset/path/sleeveRecon/TailorGAN_Garment_recon_netG_%s.pth' % opt.num_epoch,
                map_location="cuda:%d" % opt.gpuid
            ))
